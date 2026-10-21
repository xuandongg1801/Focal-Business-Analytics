"""Pure Plotly builders supporting empty frames."""
import plotly.graph_objects as go

COLORS = ['#315EFB', '#0F8A7D', '#D38B37']


def style(figure: go.Figure, title: str, height: int = 370) -> go.Figure:
    figure.update_layout(title=dict(text=title, font_size=16, y=.98, yanchor='top'), height=height,
        margin=dict(l=12, r=16, t=80, b=32), paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#35455E', size=12),
        colorway=COLORS, legend=dict(orientation='h', y=1.01, yanchor='bottom'), hovermode='x unified')
    figure.update_yaxes(gridcolor='#E6EBF2', zeroline=False)
    figure.update_xaxes(showgrid=False)
    if not figure.data:
        figure.add_annotation(text='Không có dữ liệu trong phạm vi này', x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    return figure


def trend(data, orders=False):
    fig = go.Figure()
    if len(data):
        if orders:
            fig.add_trace(go.Scatter(x=data['Tháng'], y=data['Số đơn'], mode='lines+markers', name='Đơn bán'))
        else:
            for column, color in zip(['Nền', 'Dự án xác nhận', 'Cực trị thống kê'], COLORS):
                fig.add_trace(go.Bar(x=data['Tháng'], y=data[column], name=column, marker_color=color))
            fig.update_layout(barmode='stack')
    fig.update_yaxes(title='Số đơn' if orders else 'KM ghi nhận')
    return style(fig, 'Đơn bán theo tháng' if orders else 'Sản lượng theo tháng · phân biệt nền và dự án', 420)


def ranking(data, label: str, amount: str, title: str, limit: int = 10):
    fig = go.Figure()
    d = data.dropna(subset=[amount]).nlargest(limit, amount).iloc[::-1]
    if len(d):
        fig.add_trace(go.Bar(x=d[amount], y=d[label], orientation='h', marker_color=COLORS[0]))
    fig.update_xaxes(title=amount)
    return style(fig, title)


def forecast(history, future):
    fig = go.Figure()
    for frame, x, y, label, color in [(history, 'month', 'km', 'Nền quan sát', COLORS[0]),
                                     (future, 'thang', 'du_bao_km', 'Dự báo', COLORS[1])]:
        if len(frame):
            fig.add_trace(go.Scatter(x=frame[x], y=frame[y], mode='lines+markers', name=label, line=dict(color=color)))
    fig.update_yaxes(title='KM nền')
    return style(fig, 'Lịch sử và dự báo từ mô hình', 420)
