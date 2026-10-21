import streamlit as st
from ..components.info_box import page_header, info_box
from ..components.charts import model_bars, curves, confusion
from ..utils.data_loader import table, metadata
from ..utils.formatting import METRICS, model_name, selection_label

def render():
    page_header('So sánh mô hình','3 Machine Learning · 1 Deep Learning · Cùng một phương pháp đánh giá.')
    frozen=metadata();info_box(model_name(frozen['selected_model']), selection_label(frozen))
    phase=st.radio('Giai đoạn đánh giá',['Validation','Test'],horizontal=True)
    prefix=phase.lower();comp=table('model_comparison.csv')
    cols=['model']+[f'{prefix}_{k}' for k in METRICS]
    view=comp[cols].rename(columns={'model':'Model',**{f'{prefix}_{k}':v for k,v in METRICS.items()}})
    view['Model']=view.Model.map(model_name)
    st.dataframe(view.style.format({v:'{:.3f}' for v in METRICS.values()}),hide_index=True,width='stretch')
    st.download_button('Tải bảng so sánh CSV',view.to_csv(index=False).encode('utf-8-sig'),f'model_comparison_{prefix}.csv','text/csv')
    st.caption('PR-AUC được báo cáo bằng Average Precision (AP).')
    model_bars(view[['Model','F1','Macro-F1','ROC-AUC','PR-AUC']])
    predictions=table('validation_predictions.csv' if prefix=='validation' else 'transaction_approval_predictions.csv')
    curves(predictions,comp.model.tolist(),'chot_don' if prefix=='validation' else 'actual_chot_don')
    st.subheader('Đọc sai số trong bối cảnh kinh doanh')
    name=st.selectbox('Mô hình',comp.model.tolist(),format_func=model_name,index=comp.model.tolist().index(frozen['selected_model']))
    record=comp.set_index('model').loc[name]
    left,right=st.columns([1,1])
    with left: confusion(record[[f'{prefix}_{k}' for k in ['tn','fp','fn','tp']]].rename(index=lambda s:s.removeprefix(prefix+'_')))
    with right:
        st.markdown('**True Negative:** dự đoán LOST và thực tế LOST.\n\n**True Positive:** dự đoán WIN và thực tế WIN.')
        st.markdown('**False Positive:** dự đoán WIN nhưng thực tế LOST.\n\n**False Negative:** dự đoán LOST nhưng thực tế WIN.')
        st.caption(f"Threshold đã khóa trên validation: {record.threshold:.2f} · Specificity ({phase}): {record[f'{prefix}_specificity']:.1%}")
        st.caption('WIN/LOST theo presence của ba ô Product + Quantity + Unit trên mọi dòng nguồn; không xác nhận doanh thu hoặc thanh toán.')
