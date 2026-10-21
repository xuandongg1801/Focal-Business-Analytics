from datetime import date
from html import escape
import pandas as pd
import streamlit as st
from ..components.info_box import section_header
from ..components.metric_card import metric_grid
from ..components.prediction_card import prediction_card, prediction_placeholder
from ..components.charts import transaction_bars
from ..utils.data_loader import customer_codes, history, metadata, markets, schema
from ..utils.feature_builder import build_transaction, customer_summary
from ..utils.prediction import compare_all_models
from ..utils.formatting import pct, number, date_label, model_name
from approval_prediction.registry import MODEL_REGISTRY


def history_cards(features, summary, market):
    v=features.iloc[0]
    section_header('Lịch sử khách hàng', 'Chỉ tính giao dịch ở các tháng trước tháng dự báo.')
    metric_grid([('Tổng đơn lịch sử',number(summary['total_orders']),'Đơn trước tháng dự báo'),
       ('Số WIN lịch sử',number(summary['win_count']),'Mọi dòng đều có dữ liệu ở cả ba trường'),
       ('Số LOST lịch sử',number(summary['lost_count']),'Ít nhất một dòng thiếu dữ liệu'),
       ('Tỷ lệ WIN lịch sử',pct(summary['win_rate']),'WIN / tổng đơn lịch sử')])
    metric_grid([('Cách lần gần nhất',number(v.recency_months),'Tháng kể từ lần tiếp nhận trước'),
       ('Số tháng hoạt động',number(v.customer_active_months_before),'Tháng có tiếp nhận giao dịch'),
       ('Trong 3 tháng trước',number(v.orders_last_3m),'Không gồm tháng dự báo'),
       ('Trong 6 tháng trước',number(v.orders_last_6m),'Không gồm tháng dự báo')])
    st.caption('Giao dịch gần nhất: '+(date_label(summary['last_date']) if summary['last_date'] else 'Chưa có lịch sử'))
    st.caption(f'Thị trường hiện có: {market} · Chỉ tham khảo, không là đầu vào mô hình.')
    st.caption('WIN/LOST lịch sử là thống kê hồi cứu của các đơn trước tháng đã chọn. Nguồn không ghi thời điểm kết quả được biết; các số này không được dùng làm predictors.')


def render():
    st.subheader('Dự đoán khả năng chốt đơn')
    arrivals=history();frozen=metadata();codes=customer_codes()
    customers=sorted(arrivals.loc[arrivals.customer_id.ne(''),'customer_id'].unique(),key=codes.__getitem__)
    snapshot=pd.Period(arrivals.order_month.max(),freq='M')
    with st.container(border=True,key='prediction_inputs'):
        st.markdown('**Thiết lập dự đoán**')
        customer_col,month_col,year_col,model_col=st.columns([2,1.1,1,1.7])
        with customer_col:
            customer=st.selectbox('Mã khách hàng',customers+[''],index=None,placeholder='Tìm hoặc chọn mã khách hàng',
                format_func=lambda x:codes[x] if x else 'Không có mã khách nguồn',key='customer')
        with month_col:
            month=st.selectbox('Tháng dự báo',list(range(1,13)),index=snapshot.month-1,
                format_func=lambda m:f'Tháng {m:02}',key='prediction_month')
        with year_col:
            year=st.number_input('Năm',min_value=int(arrivals.order_month.str[:4].min()),max_value=snapshot.year+1,
                value=snapshot.year,step=1,format='%d',key='prediction_year')
        with model_col:
            names=list(MODEL_REGISTRY)
            selected_model=st.selectbox('Chọn mô hình',names,index=names.index(frozen['selected_model']),
                format_func=model_name,key='prediction_model')
        st.caption('Mặc định theo validation Macro-F1, ROC-AUC khi bằng điểm. Các ngày trong cùng tháng dùng chung lịch sử.')
        submitted=st.button('Phân tích giao dịch',type='primary',disabled=customer is None,width='stretch',icon=':material/auto_graph:')
        st.caption(f'Dữ liệu lịch sử đến tháng {snapshot.strftime("%m/%Y")}')
    when=date(int(year),month,1)
    if pd.Period(when,freq='M')>snapshot:
        st.warning('Thời điểm dự đoán nằm ngoài kỳ dữ liệu lịch sử hiện có.')
    context=(customer,str(when),tuple(sorted(schema()['artifact_sha256'].items())))
    saved=st.session_state.get('prediction_analysis')
    if saved and saved['identity']!=context:
        st.session_state.pop('prediction_analysis',None)
        saved=None
    if submitted:
        # Replace the whole context atomically; never reuse a stale successful result.
        st.session_state.pop('prediction_analysis',None)
        with st.spinner('Đang phân tích giao dịch...'):
            features=build_transaction(customer,when,arrivals)
            results,errors=compare_all_models(features)
            saved=dict(identity=context,features=features,results=results,errors=errors,
                summary=customer_summary(customer,when,arrivals))
            st.session_state['prediction_analysis']=saved
    if saved is None:
        prediction_placeholder()
        return
    for message in saved['errors'].values():
        st.error(message)
    results=saved['results']
    selected=results[results.model.eq(selected_model)]
    if selected.empty:
        st.warning(f'{model_name(selected_model)} chưa có kết quả. Không dùng model khác thay thế.')
    else:
        row=selected.iloc[0].to_dict()
        prediction_card(row,f'{month:02}/{year}')
        st.caption(f'{codes[customer] if customer else "Thiếu mã khách"} · Ngưỡng của mô hình đã khóa trên validation')
        export={**row,'customer_id':customer,'transaction_date':str(when)}
        export.pop('row',None)
        st.download_button('Tải kết quả CSV',pd.DataFrame([export]).to_csv(index=False).encode('utf-8-sig'),
            'transaction_prediction.csv','text/csv',icon=':material/download:')
    st.caption('WIN: mọi dòng đều có dữ liệu ở Sản phẩm, Số lượng và Đơn vị. LOST: ít nhất một dòng thiếu một trường. Nhãn không xác nhận hợp đồng, doanh thu hay thanh toán.')
    st.divider()
    st.markdown(f'<div class="customer-context"><div><span class="customer-avatar">KH</span><strong>{escape(codes[customer] if customer else "Không có mã khách nguồn")}</strong><span>Hồ sơ lịch sử</span></div><span>Trước tháng {month:02}/{year}</span></div>',unsafe_allow_html=True)
    features=saved['features']
    if features.iloc[0].prior_order_count==0:
        st.info('Chưa có lịch sử trước tháng đã chọn. Model áp dụng cùng quy tắc xử lý dữ liệu thiếu như khi training.')
    history_cards(features,saved['summary'],markets().get(customer,'Chưa xác định'))
    st.divider()
    section_header('So sánh kết quả 4 mô hình','Cùng một vector lịch sử và thời điểm; mỗi model dùng ngưỡng riêng đã khóa trên validation.')
    if not results.empty:
        view=results[['model','probability','threshold','predicted_class']].copy()
        view['model']=view.model.map(model_name)
        view=view.rename(columns={'model':'Mô hình','probability':'Khả năng WIN',
            'threshold':'Ngưỡng phân loại','predicted_class':'Dự đoán'})
        st.dataframe(view.style.format({'Khả năng WIN':'{:.1%}','Ngưỡng phân loại':'{:.1%}'}),
            hide_index=True,width='stretch',key='prediction_comparison')
        transaction_bars(results)
    else:
        st.info('Chưa có kết quả inference để so sánh. Xem lỗi từng mô hình ở trên.')
    with st.expander('Chi tiết dữ liệu đầu vào',icon=':material/table_chart:'):
        st.caption('Tỷ lệ WIN lịch sử và thị trường chỉ để tham khảo, không đưa vào model. Ngày lưu trong CSV là ngày đầu tháng dự báo.')
        st.dataframe(features,hide_index=True,width='stretch')
