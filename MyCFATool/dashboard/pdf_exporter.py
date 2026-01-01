import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import plotly.io as pio
import plotly.graph_objects as go
import pandas as pd
from PIL import Image as PILImage
import io

# Import necessary modules from the project
from MyCFATool.domain.services.fundamental_analysis_service import FundamentalAnalysisService
from MyCFATool.domain.services.technical_analysis_service import TechnicalAnalysisService
from MyCFATool.domain.services.valuation_service import ValuationService
from MyCFATool.domain.services.forecasting_service import ForecastingService
from MyCFATool.domain.repositories.financial_data_repository import FinancialDataRepository
from MyCFATool.core.config import Config
from MyCFATool.core.database import get_session

class PDFExporter:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = Config()
        self.session = get_session()
        self.repo = FinancialDataRepository(self.session)
        self.fundamental_service = FundamentalAnalysisService(self.repo)
        self.technical_service = TechnicalAnalysisService(self.repo)
        self.valuation_service = ValuationService(self.repo, self.fundamental_service)
        self.forecasting_service = ForecastingService()
        self.styles = getSampleStyleSheet()
        self.custom_styles = {
            'Title': ParagraphStyle(name='Title', fontSize=24, spaceAfter=30, alignment=TA_CENTER),
            'Heading1': ParagraphStyle(name='Heading1', fontSize=18, spaceAfter=20),
            'Heading2': ParagraphStyle(name='Heading2', fontSize=14, spaceAfter=15),
            'Normal': ParagraphStyle(name='Normal', fontSize=10, spaceAfter=12),
            'Small': ParagraphStyle(name='Small', fontSize=8, spaceAfter=8),
        }

    def generate_overview_pdf(self, ticker, period='annual'):
        """Generate comprehensive PDF for Overview tab with charts and summaries"""
        filename = f"{ticker}_overview_report.pdf"

        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []

        # Title Page
        story.append(Paragraph(f"{ticker.upper()} Comprehensive Financial Overview Report", self.custom_styles['Title']))
        story.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.custom_styles['Normal']))
        story.append(PageBreak())



        # Executive Summary
        story.append(Paragraph("Executive Summary", self.custom_styles['Heading1']))
        fiscal_date = self.repo.get_latest_fiscal_date(ticker, period)
        if fiscal_date:
            data = self.repo.get_income_statement(ticker, period, fiscal_date)
            if data:
                roe_result = self.fundamental_service.compute_return_on_equity(ticker, period, fiscal_date)
                current_ratio = self.fundamental_service.compute_current_ratio(ticker, period, fiscal_date)
                debt_ratio = self.fundamental_service.compute_debt_ratio(ticker, period, fiscal_date)

                summary_data = [
                    ['Metric', 'Value'],
                    ['Revenue', f"${data.get('revenue', 0):,.0f}"],
                    ['Net Income', f"${data.get('netIncome', 0):,.0f}"],
                    ['ROE', ".4f" if roe_result and 'value' in roe_result else 'N/A'],
                    ['Current Ratio', ".4f" if current_ratio and 'value' in current_ratio else 'N/A'],
                    ['Debt Ratio', ".4f" if debt_ratio and 'value' in debt_ratio else 'N/A'],
                    ['Fiscal Date', fiscal_date]
                ]
                table = Table(summary_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
        else:
            story.append(Paragraph("No data available for the selected ticker.", self.custom_styles['Normal']))
        story.append(PageBreak())

        # Financial Trends Charts
        story.append(Paragraph("Financial Trends", self.custom_styles['Heading1']))
        income_statements = self.repo.get_income_statements(ticker, period)
        if income_statements:
            df = pd.DataFrame(income_statements)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['fiscal_date'], y=df['revenue'], mode='lines+markers', name='Revenue'))
            fig.add_trace(go.Scatter(x=df['fiscal_date'], y=df['netIncome'], mode='lines+markers', name='Net Income'))
            fig.update_layout(title='Revenue and Net Income Trends', xaxis_title='Fiscal Date', yaxis_title='Amount ($)')
            self.add_chart_to_pdf(fig, story)
        story.append(PageBreak())

        # Ratio Trends
        story.append(Paragraph("Key Ratios Trends", self.custom_styles['Heading1']))
        ratios = self.repo.get_ratios(ticker, period)
        if ratios:
            df = pd.DataFrame(ratios)
            fig = go.Figure()
            if 'returnOnEquity' in df.columns:
                fig.add_trace(go.Scatter(x=df['fiscal_date'], y=df['returnOnEquity'], mode='lines+markers', name='ROE'))
            fig.update_layout(title='Return on Equity Trends', xaxis_title='Fiscal Date', yaxis_title='ROE')
            self.add_chart_to_pdf(fig, story)
        story.append(PageBreak())

        # Historical Price Chart
        story.append(Paragraph("Historical Stock Price", self.custom_styles['Heading1']))
        prices = self.repo.get_historical_prices(ticker)
        if prices:
            df = pd.DataFrame(prices)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['close'], mode='lines', name='Close Price'))
            fig.update_layout(title='Historical Stock Price', xaxis_title='Date', yaxis_title='Price ($)')
            self.add_chart_to_pdf(fig, story)
        story.append(PageBreak())

        # Technical Indicators Summary
        story.append(Paragraph("Technical Analysis Summary", self.custom_styles['Heading1']))
        latest_date = self.repo.get_latest_trade_date(ticker)
        if latest_date:
            indicators = []
            try:
                rsi = self.technical_service.compute_rsi(ticker, latest_date)
                if rsi and 'rsi' in rsi:
                    indicators.append(['RSI', ".2f", rsi['signal']])
            except:
                pass
            try:
                macd = self.technical_service.compute_macd(ticker, latest_date)
                if macd and 'macd' in macd:
                    indicators.append(['MACD', ".4f", macd['trend_signal']])
            except:
                pass
            if indicators:
                table_data = [['Indicator', 'Value', 'Signal']] + indicators
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
        story.append(PageBreak())

        # Forecast Summary
        story.append(Paragraph("Price Forecast", self.custom_styles['Heading1']))
        try:
            forecast = self.forecasting_service.arima_forecast(ticker, target='price', forecast_periods=5)
            if forecast and 'interpretation' in forecast:
                story.append(Paragraph(forecast['interpretation'], self.custom_styles['Normal']))
        except:
            story.append(Paragraph("Forecast not available.", self.custom_styles['Normal']))
        story.append(PageBreak())

        # Risk Assessment
        story.append(Paragraph("Risk Assessment", self.custom_styles['Heading1']))
        if fiscal_date:
            z_score = self.fundamental_service.compute_altman_z_score(ticker, period, fiscal_date)
            m_score = self.fundamental_service.compute_beneish_m_score(ticker, period, fiscal_date)
            dd = self.fundamental_service.compute_merton_dd(ticker, period, fiscal_date, rf=0.05, T=1)
            if z_score:
                risk_z = 'Safe' if z_score['z_score'] > 3 else 'Gray' if z_score['z_score'] > 1.8 else 'Distress'
                story.append(Paragraph(f"Altman Z-Score: {z_score['z_score']:.4f} ({risk_z})", self.custom_styles['Normal']))
            if m_score:
                risk_m = 'High Risk' if m_score['m_score'] > -2.22 else 'Low Risk'
                story.append(Paragraph(f"Beneish M-Score: {m_score['m_score']:.4f} ({risk_m})", self.custom_styles['Normal']))
            if dd:
                story.append(Paragraph(f"Distance to Default: {dd['dd']:.4f}", self.custom_styles['Normal']))
        story.append(PageBreak())

        doc.build(story)
        return filename

    def generate_financial_statements_pdf(self, ticker, period='annual'):
        """Generate PDF for Financial Statements tab with formatted tables"""
        filename = f"{ticker}_financial_statements_report.pdf"

        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []

        story.append(Paragraph(f"{ticker.upper()} Financial Statements Report", self.custom_styles['Title']))
        story.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.custom_styles['Normal']))
        story.append(PageBreak())

        # Income Statement
        story.append(Paragraph("Income Statement", self.custom_styles['Heading1']))
        income_statements = self.repo.get_income_statements(ticker, period)
        if income_statements:
            df = pd.DataFrame(income_statements).sort_values('fiscal_date', ascending=False).head(5)
            # Select key columns
            key_cols = ['fiscal_date', 'revenue', 'costOfRevenue', 'grossProfit', 'operatingIncome', 'netIncome']
            df_display = df[[col for col in key_cols if col in df.columns]]
            table_data = [df_display.columns.tolist()] + df_display.values.tolist()
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No income statement data available.", self.custom_styles['Normal']))
        story.append(PageBreak())

        # Balance Sheet
        story.append(Paragraph("Balance Sheet", self.custom_styles['Heading1']))
        balance_sheets = self.repo.get_balance_sheets(ticker, period)
        if balance_sheets:
            df = pd.DataFrame(balance_sheets).sort_values('fiscal_date', ascending=False).head(5)
            key_cols = ['fiscal_date', 'totalAssets', 'totalLiabilities', 'totalStockholdersEquity', 'cashAndCashEquivalents', 'totalDebt']
            df_display = df[[col for col in key_cols if col in df.columns]]
            table_data = [df_display.columns.tolist()] + df_display.values.tolist()
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No balance sheet data available.", self.custom_styles['Normal']))
        story.append(PageBreak())

        # Cash Flow Statement
        story.append(Paragraph("Cash Flow Statement", self.custom_styles['Heading1']))
        cash_flows = self.repo.get_cash_flows(ticker, period)
        if cash_flows:
            df = pd.DataFrame(cash_flows).sort_values('fiscal_date', ascending=False).head(5)
            key_cols = ['fiscal_date', 'netCashProvidedByOperatingActivities', 'netCashUsedForInvestingActivities', 'netCashUsedProvidedByFinancingActivities', 'netChangeInCash']
            df_display = df[[col for col in key_cols if col in df.columns]]
            table_data = [df_display.columns.tolist()] + df_display.values.tolist()
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No cash flow data available.", self.custom_styles['Normal']))

        doc.build(story)
        return filename

    # Similar methods for other tabs...

    def generate_valuation_pdf(self, ticker, period='annual', projection_years=5, growth_rate=3.0, risk_free=5.0, market_premium=6.0, beta=1.0):
        """Generate PDF for Valuation tab with DCF details and charts"""
        filename = f"{ticker}_valuation_report.pdf"

        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []

        story.append(Paragraph(f"{ticker.upper()} Valuation Report", self.custom_styles['Title']))
        story.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.custom_styles['Normal']))
        story.append(PageBreak())

        # DCF Valuation Results
        story.append(Paragraph("DCF Valuation Results", self.custom_styles['Heading1']))
        fiscal_date = self.repo.get_latest_fiscal_date(ticker, period)
        if fiscal_date:
            try:
                result = self.valuation_service.compute_dcf_valuation(ticker, period, fiscal_date, projection_years, growth_rate/100, risk_free/100, market_premium/100, beta)
                if result:
                    story.append(Paragraph(f"Intrinsic Value: ${result['intrinsic_value']:.2f}", self.custom_styles['Normal']))
                    story.append(Paragraph(f"WACC: {result['wacc']:.4f}", self.custom_styles['Normal']))
                    story.append(Paragraph(f"Terminal Value: ${result['terminal_value']:.2f}", self.custom_styles['Normal']))
                    story.append(Paragraph(f"Signal: {result['signal']}", self.custom_styles['Normal']))
                    story.append(Paragraph(f"Interpretation: {result['interpretation']}", self.custom_styles['Normal']))
                else:
                    story.append(Paragraph("Unable to compute DCF valuation.", self.custom_styles['Normal']))
            except Exception as e:
                story.append(Paragraph(f"Error in DCF computation: {str(e)}", self.custom_styles['Normal']))
        else:
            story.append(Paragraph("No fiscal data available.", self.custom_styles['Normal']))
        story.append(PageBreak())

        # Projected Free Cash Flows
        story.append(Paragraph("Projected Free Cash Flows", self.custom_styles['Heading1']))
        if fiscal_date:
            try:
                fcfs = self.valuation_service.project_free_cash_flows(ticker, period, fiscal_date, projection_years, growth_rate/100)
                if fcfs:
                    table_data = [['Year', 'Projected FCF']]
                    for i, fcf in enumerate(fcfs, 1):
                        table_data.append([i, f"{fcf:.2f}"])
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                else:
                    story.append(Paragraph("No FCF projections available.", self.custom_styles['Normal']))
            except Exception as e:
                story.append(Paragraph(f"Error in FCF projection: {str(e)}", self.custom_styles['Normal']))
        story.append(PageBreak())

        # Sensitivity Analysis
        story.append(Paragraph("Sensitivity Analysis", self.custom_styles['Heading1']))
        if fiscal_date:
            try:
                base_result = self.valuation_service.compute_dcf_valuation(ticker, period, fiscal_date, projection_years, growth_rate/100, risk_free/100, market_premium/100, beta)
                if base_result:
                    sensitivity = self.valuation_service.perform_sensitivity_analysis(base_result)
                    if sensitivity:
                        table_data = [['Growth Rate', 'Discount Rate', 'Intrinsic Value']]
                        for (gr, dr), val in sensitivity.items():
                            if val:
                                table_data.append([f"{gr:.1%}", f"{dr:.1%}", f"{val:.2f}"])
                        if len(table_data) > 1:
                            table = Table(table_data)
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            story.append(table)
                        else:
                            story.append(Paragraph("No sensitivity data available.", self.custom_styles['Normal']))
                    else:
                        story.append(Paragraph("Sensitivity analysis failed.", self.custom_styles['Normal']))
                else:
                    story.append(Paragraph("Base DCF failed for sensitivity.", self.custom_styles['Normal']))
            except Exception as e:
                story.append(Paragraph(f"Error in sensitivity analysis: {str(e)}", self.custom_styles['Normal']))

        doc.build(story)
        return filename

    def add_chart_to_pdf(self, fig, story):
        """Convert plotly figure to image and add to PDF story"""
        try:
            img_bytes = pio.to_image(fig, format='png', engine='kaleido')
            img = PILImage.open(io.BytesIO(img_bytes))
            img_path = '/tmp/temp_chart.png'
            img.save(img_path)
            story.append(Image(img_path, width=6*inch, height=4*inch))
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"Error adding chart to PDF: {e}")

    # Methods for other tabs can be added similarly</content>
