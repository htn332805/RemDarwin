from dash import dcc

def ticker_dropdown(options, id):
    return dcc.Dropdown(
        id=id,
        options=[{'label': opt, 'value': opt} for opt in options],
        placeholder='Select a ticker...',
    )

def period_dropdown(id):
    return dcc.Dropdown(
        id=id,
        options=[
            {'label': 'Annual', 'value': 'annual'},
            {'label': 'Quarterly', 'value': 'quarterly'}
        ],
        value='annual',
        placeholder='Select period...',
    )