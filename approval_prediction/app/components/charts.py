import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from sklearn.metrics import roc_curve, precision_recall_curve, average_precision_score, roc_auc_score
from ..utils.formatting import model_name
COLORS = ['#315EFB', '#96A6C2', '#39A59A', '#9E88C8', '#C3CAD7']

def draw(fig, title, height=330):
    fig.update_layout(title=dict(text=title, x=.05, y=.94, font=dict(size=14,color='#354E70')), height=height,
        paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
        font=dict(family='Segoe UI, Arial, sans-serif',size=11,color='#8190A6'),
        margin=dict(l=24,r=24,t=65,b=48),
        legend=dict(orientation='h',y=-.24,x=0,font=dict(size=10)),
        hoverlabel=dict(bgcolor='#FFFFFF',font_size=12,font_color='#304563',bordercolor='#DEE5F0'),
        bargap=.4,
        colorway=COLORS)
    fig.update_xaxes(showgrid=False,zeroline=False,automargin=True)
    fig.update_yaxes(gridcolor='#F0F3F8',zeroline=False,automargin=True)
    st.plotly_chart(fig, width='stretch', theme=None, config={'displayModeBar':False,'responsive':True})

def model_bars(data):
    chart=data.melt(id_vars='Model',var_name='Metric',value_name='Score')
    fig=px.bar(chart,x='Model',y='Score',color='Metric',barmode='group',color_discrete_sequence=COLORS)
    fig.update_yaxes(range=[0,1],title='Điểm số')
    draw(fig,'Đối chiếu hiệu quả mô hình',380)

def curves(predictions,names,target):
    y=predictions[target]
    if y.nunique()<2:
        st.info('Không đủ cả hai lớp để vẽ ROC/PR.'); return
    roc,pr=go.Figure(),go.Figure()
    for n,color in zip(names,COLORS):
        p=predictions[f'prob_{n}'];fpr,tpr,_=roc_curve(y,p)
        precision,recall,_=precision_recall_curve(y,p)
        roc.add_trace(go.Scatter(x=fpr,y=tpr,mode='lines',name=f'{model_name(n)} · {roc_auc_score(y,p):.3f}',line=dict(color=color,width=2)))
        pr.add_trace(go.Scatter(x=recall,y=precision,mode='lines',name=f'{model_name(n)} · {average_precision_score(y,p):.3f}',line=dict(color=color,width=2,shape='hv')))
    roc.add_shape(type='line',x0=0,y0=0,x1=1,y1=1,line=dict(color='#CBD5E1',dash='dot'))
    for f,x,ylabel in [(roc,'False positive rate','True positive rate'),(pr,'Recall','Precision')]:
        f.update_xaxes(range=[0,1],title=x);f.update_yaxes(range=[0,1.05],title=ylabel)
    left,right=st.columns(2)
    with left: draw(roc,'ROC · legend hiển thị AUC',420)
    with right: draw(pr,'Precision–Recall · legend hiển thị AP',420)

def confusion(row):
    z=[[int(row.tn),int(row.fp)],[int(row.fn),int(row.tp)]]
    fig=go.Figure(go.Heatmap(z=z,x=['Dự đoán LOST','Dự đoán WIN'],y=['Thực tế LOST','Thực tế WIN'],
       text=[[f'TN · {z[0][0]}',f'FP · {z[0][1]}'],[f'FN · {z[1][0]}',f'TP · {z[1][1]}']],texttemplate='%{text}',
       colorscale=[[0,'#EFF6FF'],[1,'#2563EB']],showscale=False))
    fig.update_yaxes(autorange='reversed')
    draw(fig,'Confusion matrix',340)

def importance(data):
    d=data.head(10).iloc[::-1]
    fig=go.Figure(go.Bar(x=d.importance,y=d.feature,orientation='h',marker_color=COLORS[0],error_x=dict(type='data',array=d['std'],color='#94A3B8')))
    fig.update_xaxes(title='Mức giảm ROC-AUC khi hoán vị biến')
    draw(fig,'Permutation importance · validation',440)

def transaction_bars(results):
    fig=go.Figure(go.Bar(x=results.probability,y=results.model.map(model_name),orientation='h',marker_color=COLORS[0],
       text=[f'{v:.1%}' for v in results.probability],textposition='outside',cliponaxis=False))
    fig.update_xaxes(range=[0,1],tickformat='.0%',title='Khả năng WIN')
    draw(fig,'Cùng một giao dịch · bốn mô hình',280)
