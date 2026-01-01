import plotly.graph_objects as go

def create_line_chart(df, x_col, y_col, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], mode='lines'))
    fig.update_layout(title=title)
    return fig

def create_bar_chart(df, x_col, y_col, title):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df[x_col], y=df[y_col]))
    fig.update_layout(title=title)
    return fig