from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import numpy as np
import io
import base64
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)

# Load the model
model = load_model("C:/Users/istifa/Downloads/PLN/modules/gru_model.h5")
scaler = MinMaxScaler()

# Load CSVs
lstm_df = pd.read_csv('C:/Users/istifa/Downloads/PLN/csv/lstm_pred_result.csv')
xgboost_df = pd.read_csv('C:/Users/istifa/Downloads/PLN/csv/xgboost_pred_result.csv')
gru_df = pd.read_csv('C:/Users/istifa/Downloads/PLN/csv/gru_pred_result.csv')

# Assuming the columns are named 'datetime', 'actual', 'predicted'
lstm_df['datetime'] = pd.to_datetime(lstm_df['datetime'])
xgboost_df['datetime'] = pd.to_datetime(xgboost_df['datetime'])
gru_df['datetime'] = pd.to_datetime(gru_df['datetime'])

# Assuming the columns are named 'datetime', 'actual', 'prediction'
lstm_df['datetime'] = pd.to_datetime(lstm_df['datetime'])
xgboost_df['datetime'] = pd.to_datetime(xgboost_df['datetime'])
gru_df['datetime'] = pd.to_datetime(gru_df['datetime'])

def create_plot():
    traces = []

    # Actual vs LSTM
    trace_actual_lstm = go.Scatter(
        x=lstm_df['datetime'], y=lstm_df['actual'],
        mode='lines', name='Actual',
        line=dict(color='blue'),  # Set line color for Actual
        visible=False
    )
    trace_pred_lstm = go.Scatter(
        x=lstm_df['datetime'], y=lstm_df['prediction'],
        mode='lines', name='Predicted LSTM',
        line=dict(color='green'),  # Set line color for Predicted LSTM
        visible=False
    )
    
    # Actual vs XGBoost
    trace_actual_xgboost = go.Scatter(
        x=xgboost_df['datetime'], y=xgboost_df['actual'],
        mode='lines', name='Actual',
        line=dict(color='blue'),  # Same color as above to match the actual line
        visible=False
    )
    trace_pred_xgboost = go.Scatter(
        x=xgboost_df['datetime'], y=xgboost_df['prediction'],
        mode='lines', name='Predicted XGBoost',
        line=dict(color='red'),  # Set line color for Predicted XGBoost
        visible=False
    )
    
    # Actual vs GRU
    trace_actual_gru = go.Scatter(
        x=gru_df['datetime'], y=gru_df['actual'],
        mode='lines', name='Actual',
        line=dict(color='blue'),  # Same color as above to match the actual line
        visible=False
    )
    trace_pred_gru = go.Scatter(
        x=gru_df['datetime'], y=gru_df['prediction'],
        mode='lines', name='Predicted GRU',
        line=dict(color='orange'),  # Set line color for Predicted GRU
        visible=False
    )

    # LSTM vs XGBoost vs GRU (Predictions Only)
    trace_pred_lstm_only = go.Scatter(
        x=lstm_df['datetime'], y=lstm_df['prediction'],
        mode='lines', name='Predicted LSTM',
        line=dict(color='green'),  # Same color as the LSTM prediction line
        visible=False
    )
    trace_pred_xgboost_only = go.Scatter(
        x=xgboost_df['datetime'], y=xgboost_df['prediction'],
        mode='lines', name='Predicted XGBoost',
        line=dict(color='red'),  # Same color as the XGBoost prediction line
        visible=False
    )
    trace_pred_gru_only = go.Scatter(
        x=gru_df['datetime'], y=gru_df['prediction'],
        mode='lines', name='Predicted GRU',
        line=dict(color='orange'),  # Same color as the GRU prediction line
        visible=False
    )

    traces.extend([
        trace_actual_lstm, trace_pred_lstm,
        trace_actual_xgboost, trace_pred_xgboost,
        trace_actual_gru, trace_pred_gru,
        trace_pred_lstm_only, trace_pred_xgboost_only, trace_pred_gru_only
    ])

    layout = go.Layout(
        title='Comparison of Actual vs Predicted',
        xaxis=dict(title='Datetime'),
        yaxis=dict(title='Value'),
        updatemenus=[dict(
            type="buttons",
            direction="down",
            buttons=list([
                dict(
                    args=[{'visible': [True, True, False, False, False, False, False, False, False]}],
                    label="Actual vs LSTM",
                    method="update"
                ),
                dict(
                    args=[{'visible': [False, False, True, True, False, False, False, False, False]}],
                    label="Actual vs XGBoost",
                    method="update"
                ),
                dict(
                    args=[{'visible': [False, False, False, False, True, True, False, False, False]}],
                    label="Actual vs GRU",
                    method="update"
                ),
                dict(
                    args=[{'visible': [True, False, False, False, False, False, True, True, True]}],
                    label="LSTM vs XGBoost vs GRU",
                    method="update"
                )
            ]),
            showactive=True,
        )]
    )

    fig = go.Figure(data=traces, layout=layout)
    plot_div = pio.to_html(fig, full_html=False)

    return plot_div

@app.route('/')
def index():
    plot_div = create_plot()
    return render_template('index.html', plot_div=plot_div, title='Comparative Chart')

@app.route('/tables')
def tables():
    # Remove specific bootstrap classes
    lstm_table = lstm_df.to_html(classes="data")
    xgboost_table = xgboost_df.to_html(classes="data")
    gru_table = gru_df.to_html(classes="data")
    
    return render_template('tables.html', 
                           lstm_table=lstm_table, 
                           xgboost_table=xgboost_table, 
                           gru_table=gru_table, 
                           title='Table Results')

@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    if request.method == 'POST':
        # Check if the file is uploaded
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        # Read the CSV file for future predictions
        df_30_days_future = pd.read_csv(file)
        df_30_days_future['Datetime'] = pd.to_datetime(df_30_days_future['Datetime'])
        df_30_days_future.set_index('Datetime', inplace=True)
        
        # Ensure 'MW' column exists and set it to 0 initially
        if 'MW' not in df_30_days_future.columns:
            df_30_days_future['MW'] = 0
        
        df_30_days_future = df_30_days_future[["Suhu", "MW"]]
        
        # Load the historical data from the specified path
        historical_path = r'C:\Users\istifa\Downloads\PLN\modules\historical.csv'
        df_historical = pd.read_csv(historical_path)
        df_historical['Datetime'] = pd.to_datetime(df_historical['Datetime'])
        df_historical.set_index('Datetime', inplace=True)

        # Ensure 'MW' column exists in the historical data
        if 'MW' not in df_historical.columns:
            df_historical['MW'] = 0

        # Take the last 30 days of historical data
        df_30_days_past = df_historical.iloc[-30:, :]
        
        # Fit the scaler on the historical data
        scaler.fit(df_30_days_past)

        # Now you can transform both the past and future data
        old_scaled_array = scaler.transform(df_30_days_past)
        new_scaled_array = scaler.transform(df_30_days_future)
        
        new_scaled_df = pd.DataFrame(new_scaled_array, columns=["Suhu", "MW"])
        new_scaled_df.iloc[:, 1] = np.nan
        
        full_df = pd.concat([pd.DataFrame(old_scaled_array, columns=["Suhu", "MW"]), new_scaled_df]).reset_index(drop=True)
        full_df.index = list(range(len(old_scaled_array))) + list(df_30_days_future.index)
        
        # Forecasting
        full_df_scaled_array = full_df.values
        all_data = []
        time_step = 30
        for i in range(time_step, len(full_df_scaled_array)):
            data_x = []
            data_x.append(full_df_scaled_array[i-time_step :i, 0:full_df_scaled_array.shape[1]])
            data_x = np.array(data_x)
            prediction = model.predict(data_x)
            all_data.append(prediction)
            full_df.iloc[i, 1] = prediction
        
        new_array = np.array(all_data)
        new_array = new_array.reshape(-1, 1)
        prediction_copies_array = np.repeat(new_array, 2, axis=-1)
        y_pred_future_30_days = scaler.inverse_transform(np.reshape(prediction_copies_array, (len(new_array), 2)))[:, 1]
        
        # Create a DataFrame for results
        df_hasil_forecast = pd.DataFrame({
            'Datetime': df_30_days_future.index,
            'Suhu': df_30_days_future['Suhu'],
            'Predicted Load': y_pred_future_30_days
        })

        # Reset index to avoid duplicate 'Datetime' columns
        df_hasil_forecast.reset_index(drop=True, inplace=True)

        # Convert DataFrame to HTML table
        df_hasil_forecast_html = df_hasil_forecast.to_html(classes='data', header="true")

        # Plotting the forecast with Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_hasil_forecast['Datetime'], 
                                 y=df_hasil_forecast['Predicted Load'], 
                                 mode='lines', 
                                 name='Forecast'))

        fig.update_layout(title='Forecast for the Next 30 Days',
                          xaxis_title='Datetime',
                          yaxis_title='MW')

        # Convert plot to HTML
        plot_html = pio.to_html(fig, full_html=False)
        
        # Render the results in the template
        return render_template('forecast.html', 
                               title='Forecasting',
                               plot_html=plot_html,
                               tables=df_hasil_forecast_html)
    
    # If GET request, render the forecast page with upload form
    return render_template('forecast.html', title='Forecasting')


if __name__ == '__main__':
    app.run(debug=True)
