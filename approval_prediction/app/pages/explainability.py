import streamlit as st
from ..components.info_box import page_header, info_box
from ..components.charts import importance
from ..utils.data_loader import table, metadata
from ..utils.formatting import model_name

def render():
    page_header('Giải thích mô hình','Khám phá những thông tin liên quan đến kết quả dự báo.')
    data=table('feature_importance.csv')
    left,right=st.columns([1.7,1])
    with left:
        importance(data)
    with right:
        info_box('Cách đọc','Biến có importance cao hơn nghĩa là việc xáo trộn thông tin đó làm giảm ROC-AUC nhiều hơn. Điều này không chứng minh quan hệ nhân quả.')
        st.markdown('**'+model_name(metadata()['selected_model'])+'** · permutation importance trên validation.')
        st.caption('Top 10 biến theo mức giảm ROC-AUC. Thanh sai số là độ lệch chuẩn qua các lần hoán vị. Giá trị gần 0, âm hoặc sai số lớn cho thấy tín hiệu yếu/không ổn định. Đây là giải thích toàn cục, không phải giải thích riêng một giao dịch.')
    st.subheader('Từ điển feature')
    dictionary=table('feature_dictionary.csv')
    only=st.toggle('Chỉ hiển thị feature được dùng',value=True)
    if only: dictionary=dictionary[dictionary.used_in_model.eq(True)]
    view=dictionary[['feature_name','description','available_at_prediction_time','leakage_risk','used_in_model']].rename(columns={
       'feature_name':'Feature','description':'Ý nghĩa','available_at_prediction_time':'Có trước giao dịch?',
       'leakage_risk':'Rủi ro leakage','used_in_model':'Được sử dụng'})
    st.dataframe(view,hide_index=True,width='stretch')
    info_box('Ranh giới thông tin','Model chỉ dùng lịch sử tiếp nhận đơn của các tháng trước và thời gian giao dịch. Không dùng sản phẩm, số lượng, đơn vị, giá, WO hoặc mức hoàn thiện của giao dịch hiện tại.')
