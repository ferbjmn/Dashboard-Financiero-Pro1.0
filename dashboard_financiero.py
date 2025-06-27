import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import time
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero Avanzado",
    layout="wide",
    page_icon="📊"
)

# Cache con expiración de 6 horas
@st.cache_data(ttl=21600)
def obtener_datos_cacheados(ticker):
    return get_data(ticker)

# Parámetros WACC
Rf = 0.0435
Rm = 0.085
Tc = 0.21

def calcular_wacc(info, balance_sheet):
    try:
        beta = info.get("beta")
        price = info.get("currentPrice")
        shares = info.get("sharesOutstanding")
        market_cap = price * shares if price and shares else None
        lt_debt = balance_sheet.loc["Long Term Debt", :].iloc[0] if "Long Term Debt" in balance_sheet.index else 0
        st_debt = balance_sheet.loc["Short Long Term Debt", :].iloc[0] if "Short Long Term Debt" in balance_sheet.index else 0
        total_debt = lt_debt + st_debt
        Re = Rf + beta * (Rm - Rf) if beta is not None else None
        Rd = 0.055 if total_debt > 0 else 0
        E = market_cap
        D = total_debt

        if None in [Re, E, D] or E + D == 0:
            return None, total_debt

        wacc = (E / (E + D)) * Re + (D / (E + D)) * Rd * (1 - Tc)
        return wacc, total_debt
    except:
        return None, None

def calcular_crecimiento_historico(financials, metric):
    try:
        if metric not in financials.index:
            return None
        datos = financials.loc[metric].dropna().iloc[:4]
        if len(datos) < 2:
            return None
        primer_valor = datos.iloc[-1]
        ultimo_valor = datos.iloc[0]
        años = len(datos) - 1
        if primer_valor == 0:
            return None
        cagr = (ultimo_valor / primer_valor) ** (1 / años) - 1
        return cagr
    except:
        return None

def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        price = info.get("currentPrice")
        name = info.get("longName")
        sector = info.get("sector")
        country = info.get("country")
        industry = info.get("industry")

        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        dividend = info.get("dividendRate")
        dividend_yield = info.get("dividendYield")
        payout = info.get("payoutRatio")
        roa = info.get("returnOnAssets")
        roe = info.get("returnOnEquity")
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")
        ltde = info.get("longTermDebtEquity")
        de = info.get("debtToEquity")
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("netMargins")

        fcf = cf.loc["Total Cash From Operating Activities"].iloc[0] if "Total Cash From Operating Activities" in cf.index else None
        shares = info.get("sharesOutstanding")
        pfcf = price / (fcf / shares) if fcf and shares else None

        ebit = fin.loc["EBIT"].iloc[0] if "EBIT" in fin.index else None
        equity = bs.loc["Total Stockholder Equity"].iloc[0] if "Total Stockholder Equity" in bs.index else None
        wacc, total_debt = calcular_wacc(info, bs)
        capital_invertido = total_debt + equity if total_debt and equity else None
        roic = ebit / capital_invertido if ebit and capital_invertido else None
        eva = roic - wacc if roic and wacc else None

        revenue_growth = calcular_crecimiento_historico(fin, "Total Revenue")
        eps_growth = calcular_crecimiento_historico(fin, "Net Income")
        fcf_growth = calcular_crecimiento_historico(cf, "Free Cash Flow") or calcular_crecimiento_historico(cf, "Total Cash From Operating Activities")

        cash_ratio = info.get("cashRatio")
        operating_cash_flow = cf.loc["Total Cash From Operating Activities"].iloc[0] if "Total Cash From Operating Activities" in cf.index else None
        current_liabilities = bs.loc["Total Current Liabilities"].iloc[0] if "Total Current Liabilities" in bs.index else None
        cash_flow_ratio = operating_cash_flow / current_liabilities if operating_cash_flow and current_liabilities else None

        return {
            "Ticker": ticker,
            "Nombre": name,
            "Sector": sector,
            "País": country,
            "Industria": industry,
            "Precio": price,
            "P/E": pe,
            "P/B": pb,
            "P/FCF": pfcf,
            "Dividend Year": dividend,
            "Dividend Yield %": dividend_yield,
            "Payout Ratio": payout,
            "ROA": roa,
            "ROE": roe,
            "Current Ratio": current_ratio,
            "Quick Ratio": quick_ratio,
            "LtDebt/Eq": ltde,
            "Debt/Eq": de,
            "Oper Margin": op_margin,
            "Profit Margin": profit_margin,
            "WACC": wacc,
            "ROIC": roic,
            "EVA": eva,
            "Deuda Total": total_debt,
            "Patrimonio Neto": equity,
            "Revenue Growth": revenue_growth,
            "EPS Growth": eps_growth,
            "FCF Growth": fcf_growth,
            "Cash Ratio": cash_ratio,
            "Cash Flow Ratio": cash_flow_ratio,
            "Operating Cash Flow": operating_cash_flow,
            "Current Liabilities": current_liabilities,
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Configuración inicial
if "resultados" not in st.session_state:
    st.session_state["resultados"] = {}

# Sidebar para configuración
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Selector de tema
    theme = st.selectbox("Tema visual", ["Light", "Dark"])
    
    # Configuración de análisis
    st.subheader("Opciones de Análisis")
    max_tickers = st.slider("Máximo de tickers", 5, 50, 15)
    delay = st.slider("Delay entre requests (seg)", 1.0, 5.0, 2.5)
    
    # Información de la sesión
    st.subheader("Información de Sesión")
    st.write(f"Tickers analizados: {len(st.session_state['resultados'])}")
    if st.button("Limpiar caché"):
        st.cache_data.clear()
        st.session_state["resultados"] = {}
        st.rerun()

# Título principal
st.title("📊 Dashboard de Análisis Financiero Avanzado")

# Input de tickers en el main
tickers_input = st.text_area(
    "🔎 Ingresa tickers separados por coma", 
    "AAPL,MSFT,GOOGL,TSLA,AMZN",
    help=f"Máximo {max_tickers} tickers por análisis"
)

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()][:max_tickers]

if st.button("🔍 Analizar", type="primary"):
    nuevos = [t for t in tickers if t not in st.session_state["resultados"]]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, t in enumerate(nuevos):
        status_text.text(f"⏳ Procesando {t} ({i+1}/{len(nuevos)})...")
        st.session_state["resultados"][t] = obtener_datos_cacheados(t)
        progress_bar.progress((i + 1) / len(nuevos))
        time.sleep(delay)  # Delay configurable
    
    status_text.success("✅ Análisis completado!")
    time.sleep(1)
    status_text.empty()

# Sistema de pestañas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Resumen General", 
    "💳 Análisis de Deuda", 
    "💡 Creación de Valor", 
    "📈 Crecimiento", 
    "💰 Liquidez"
])

# Pestaña 1: Resumen General
with tab1:
    if st.session_state["resultados"]:
        datos = list(st.session_state["resultados"].values())
        columnas_mostrar = [
            "Ticker", "Sector", "Industria", "País", "Precio", 
            "P/E", "P/B", "P/FCF", "Dividend Year", "Dividend Yield %", 
            "Payout Ratio", "ROA", "ROE", "Current Ratio", "Quick Ratio", 
            "LtDebt/Eq", "Debt/Eq", "Oper Margin", "Profit Margin", 
            "WACC", "ROIC", "EVA"
        ]
        df = pd.DataFrame(datos)[columnas_mostrar].dropna(how='all', axis=1)
        
        # Formateo de porcentajes
        porcentajes = ["Dividend Yield %", "ROA", "ROE", "Oper Margin", "Profit Margin", "WACC", "ROIC", "EVA"]
        for col in porcentajes:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/D")
        
        st.dataframe(
            df.style.highlight_max(subset=df.select_dtypes(include='number').columns, 
            color='lightgreen'
        ).highlight_min(
            subset=df.select_dtypes(include='number').columns, 
            color='#ffcccb'
        ), use_container_width=True)
        
        # Gráfico rápido de comparación
        if len(df) > 1:
            st.subheader("Comparación Rápida")
            metricas_comparar = st.multiselect(
                "Selecciona métricas para comparar",
                options=["P/E", "P/B", "ROE", "Current Ratio", "Debt/Eq"],
                default=["P/E", "ROE"]
            )
            
            if metricas_comparar:
                fig, ax = plt.subplots(figsize=(10, 5))
                df.set_index("Ticker")[metricas_comparar].plot(kind='bar', ax=ax)
                ax.set_title("Comparación entre Empresas")
                ax.legend(title="Métricas")
                st.pyplot(fig)

# Pestaña 2: Análisis de Deuda
with tab2:
    st.markdown("## 💳 Análisis de Solvencia de Deuda")
    
    for detalle in st.session_state["resultados"].values():
        if "Error" in detalle:
            continue

        nombre = detalle.get("Nombre", detalle["Ticker"])
        deuda = detalle.get("Deuda Total", 0)
        activos = detalle.get("Total Activos", 0)
        efectivo = detalle.get("Cash And Cash Equivalents", 0)
        patrimonio = detalle.get("Patrimonio Neto", 0)
        ebit = detalle.get("EBIT", 0)
        intereses = detalle.get("Interest Expense", 0)
        flujo_operativo = detalle.get("Operating Cash Flow", 0)

        # Ratios
        deuda_patrimonio = deuda / patrimonio if patrimonio else None
        deuda_activos = deuda / activos if activos else None
        cobertura_intereses = ebit / intereses if intereses else None
        flujo_deuda = flujo_operativo / deuda if deuda else None
        deuda_neta_ebitda = (deuda - efectivo) / ebit if ebit else None

        # DataFrame de ratios
        df_ratios = pd.DataFrame({
            "Indicador": [
                "Debt-to-Equity", "Debt-to-Assets", "Interest Coverage",
                "Cash Flow to Debt", "Net Debt to EBITDA"
            ],
            "Valor": [
                deuda_patrimonio, deuda_activos, cobertura_intereses,
                flujo_deuda, deuda_neta_ebitda
            ]
        })

        # Visualización
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"### {nombre}")
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.bar(df_ratios["Indicador"], df_ratios["Valor"], color="skyblue")
            ax.set_title("Ratios de Deuda")
            ax.tick_params(axis='x', rotation=45)
            st.pyplot(fig)
        
        with col2:
            st.dataframe(df_ratios.set_index("Indicador"), use_container_width=True)
            
            # Conclusiones
            sostenibilidad = True
            alertas = []
            
            if deuda_patrimonio is not None and deuda_patrimonio >= 1:
                alertas.append("🔻 Deuda/Patrimonio > 1 indica exceso de apalancamiento.")
                sostenibilidad = False
            if deuda_activos is not None and deuda_activos >= 0.5:
                alertas.append("🔻 Deuda/Activos > 0.5 indica endeudamiento elevado.")
                sostenibilidad = False
            if cobertura_intereses is not None and cobertura_intereses < 3:
                alertas.append("🔻 Cobertura de intereses < 3 sugiere dificultad para pagar intereses.")
                sostenibilidad = False
            if flujo_deuda is not None and flujo_deuda < 0.2:
                alertas.append("🔻 Flujo operativo/deuda < 0.2 indica margen ajustado para pagos.")
                sostenibilidad = False
            if deuda_neta_ebitda is not None and deuda_neta_ebitda > 3:
                alertas.append("🔻 Deuda neta/EBITDA > 3 implica presión financiera.")
                sostenibilidad = False

            if sostenibilidad:
                st.success("✅ La estructura de deuda es saludable.")
            else:
                st.error("⚠️ La empresa presenta señales de endeudamiento riesgoso.")
                for alerta in alertas:
                    st.markdown(alerta)

        st.markdown("---")

# Pestaña 3: Creación de Valor
with tab3:
    st.markdown("## 💡 Análisis de Creación de Valor (WACC vs ROIC)")
    
    for detalle in st.session_state["resultados"].values():
        if "Error" in detalle:
            continue

        nombre = detalle.get("Nombre", detalle["Ticker"])
        wacc = detalle.get("WACC")
        roic = detalle.get("ROIC")
        eva = detalle.get("EVA")

        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"### {nombre}")
            
            if wacc and roic:
                fig, ax = plt.subplots(figsize=(4, 3))
                ax.bar(["ROIC", "WACC"], [roic * 100, wacc * 100],
                      color=["green" if roic > wacc else "red", "gray"])
                ax.set_ylabel("%")
                ax.set_title("ROIC vs WACC")
                st.pyplot(fig)
            else:
                st.warning("Datos insuficientes para el análisis")
        
        with col2:
            if wacc and roic:
                st.metric("WACC", f"{wacc:.2%}")
                st.metric("ROIC", f"{roic:.2%}", delta=f"{(roic-wacc):.2%}" if roic and wacc else None)
                st.metric("EVA", f"{eva:.2%}" if eva else "N/D")
                
                if roic > wacc:
                    st.success("✅ La empresa crea valor (ROIC > WACC)")
                else:
                    st.error("❌ La empresa destruye valor (ROIC < WACC)")
            else:
                st.info("No hay suficientes datos para calcular WACC/ROIC")

        st.markdown("---")

# Pestaña 4: Crecimiento
with tab4:
    st.markdown("## 📈 Análisis de Crecimiento Histórico")
    
    for detalle in st.session_state["resultados"].values():
        if "Error" in detalle:
            continue
        
        nombre = detalle.get("Nombre", detalle["Ticker"])
        revenue_growth = detalle.get("Revenue Growth")
        eps_growth = detalle.get("EPS Growth")
        fcf_growth = detalle.get("FCF Growth")

        st.markdown(f"### {nombre}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if None not in [revenue_growth, eps_growth, fcf_growth]:
                fig, ax = plt.subplots(figsize=(4, 3))
                metrics = ["Ingresos", "EPS", "FCF"]
                growth_rates = [revenue_growth, eps_growth, fcf_growth]
                colors = ["green" if g > 0 else "red" for g in growth_rates]
                
                ax.bar(metrics, [g * 100 for g in growth_rates], color=colors)
                ax.set_ylabel("CAGR (%)")
                ax.set_title("Tasas de Crecimiento")
                st.pyplot(fig)
            else:
                st.warning("Datos incompletos para crecimiento")
        
        with col2:
            if None not in [revenue_growth, eps_growth, fcf_growth]:
                st.metric("Crecimiento Ingresos", f"{revenue_growth:.2%}")
                st.metric("Crecimiento EPS", f"{eps_growth:.2%}")
                st.metric("Crecimiento FCF", f"{fcf_growth:.2%}")
                
                if revenue_growth > 0 and eps_growth > 0 and fcf_growth > 0:
                    st.success("Crecimiento consistente en todas las métricas")
                elif revenue_growth > 0 and eps_growth > 0:
                    st.info("Crecimiento en ingresos y beneficios")
                elif any(g < 0 for g in [revenue_growth, eps_growth, fcf_growth]):
                    st.warning("Crecimiento negativo en algunas métricas")
            else:
                st.info("Datos de crecimiento no disponibles")

        st.markdown("---")

# Pestaña 5: Liquidez
with tab5:
    st.markdown("## 💰 Análisis de Liquidez Avanzada")
    
    for detalle in st.session_state["resultados"].values():
        if "Error" in detalle:
            continue
        
        nombre = detalle.get("Nombre", detalle["Ticker"])
        current_ratio = detalle.get("Current Ratio")
        quick_ratio = detalle.get("Quick Ratio")
        cash_ratio = detalle.get("Cash Ratio")
        cash_flow_ratio = detalle.get("Cash Flow Ratio")
        operating_cash_flow = detalle.get("Operating Cash Flow")
        current_liabilities = detalle.get("Current Liabilities")

        st.markdown(f"### {nombre}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            ratios = {
                "Current Ratio": current_ratio,
                "Quick Ratio": quick_ratio,
                "Cash Ratio": cash_ratio,
                "Cash Flow Ratio": cash_flow_ratio
            }
            
            df_ratios = pd.DataFrame.from_dict(ratios, orient='index', columns=['Valor'])
            st.dataframe(df_ratios, use_container_width=True)
        
        with col2:
            if None not in [current_ratio, quick_ratio, cash_ratio, cash_flow_ratio]:
                fig, ax = plt.subplots(figsize=(4, 3))
                ax.bar(ratios.keys(), ratios.values(), 
                      color=["green" if v > 1 else "orange" if v > 0.5 else "red" for v in ratios.values()])
                ax.set_ylabel("Ratio")
                ax.set_title("Ratios de Liquidez")
                ax.tick_params(axis='x', rotation=45)
                st.pyplot(fig)
                
                # Evaluación
                if all([current_ratio > 1.5, quick_ratio > 1, cash_ratio > 0.5, cash_flow_ratio > 0.4]):
                    st.success("🛡️ Excelente posición de liquidez")
                elif any([current_ratio < 1, quick_ratio < 0.5, cash_ratio < 0.2, cash_flow_ratio < 0.2]):
                    st.error("⚠️ Posición de liquidez preocupante")
                else:
                    st.info("🔄 Liquidez aceptable")
            else:
                st.warning("Datos incompletos para análisis de liquidez")

        st.markdown("---")

# Pie de página
st.markdown("---")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
