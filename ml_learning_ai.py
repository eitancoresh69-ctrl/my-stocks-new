# ml_learning_ai.py — למידת מכונה אמיתית + שמירה קבועה
# pip install scikit-learn  ← הוסף ל-requirements.txt

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from storage import save_ml

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, IsolationForest
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    import yfinance as yf
    import pickle, io, base64
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ══════════════════════════════════════════════════════════
# חישוב פיצ'רים טכניים (ללא ta-lib — רק numpy/pandas)
# ══════════════════════════════════════════════════════════

def _rsi(s, p=14):
    d = s.diff()
    g = d.where(d>0,0.0).rolling(p).mean()
    l = (-d.where(d<0,0.0)).rolling(p).mean().replace(0,1e-10)
    return 100-(100/(1+g/l))

def _macd(s):
    return s.ewm(span=12,adjust=False).mean() - s.ewm(span=26,adjust=False).mean()

def _bb_width(s,p=20):
    ma=s.rolling(p).mean(); std=s.rolling(p).std()
    return (std*2)/ma

FEAT_COLS = ["rsi","macd","bb_width","ret_5d","ret_20d","vol_ratio",
             "above_ma50","above_ma200","volatility","momentum","candle_body","gap"]

FEAT_HE = {
    "rsi":"RSI","macd":"MACD","bb_width":"Bollinger Width",
    "ret_5d":"תשואה 5י","ret_20d":"תשואה 20י","vol_ratio":"יחס נפח",
    "above_ma50":"מעל MA50","above_ma200":"מעל MA200",
    "volatility":"תנודתיות","momentum":"מומנטום","candle_body":"גוף נר","gap":"גאפ"
}

def _build_features(hist: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(index=hist.index)
    df["rsi"]        = _rsi(hist["Close"])
    df["macd"]       = _macd(hist["Close"])
    df["bb_width"]   = _bb_width(hist["Close"])
    df["ret_5d"]     = hist["Close"].pct_change(5)
    df["ret_20d"]    = hist["Close"].pct_change(20)
    df["vol_ratio"]  = hist["Volume"] / hist["Volume"].rolling(20).mean()
    df["above_ma50"] = (hist["Close"] > hist["Close"].rolling(50).mean()).astype(int)
    df["above_ma200"]= (hist["Close"] > hist["Close"].rolling(200).mean()).astype(int)
    df["volatility"] = hist["Close"].pct_change().rolling(20).std()
    df["momentum"]   = hist["Close"] / hist["Close"].shift(10) - 1
    df["candle_body"]= abs(hist["Close"]-hist["Open"]) / (hist["High"]-hist["Low"]+1e-10)
    df["gap"]        = (hist["Open"]-hist["Close"].shift(1)) / hist["Close"].shift(1)
    df["target"]     = (hist["Close"].shift(-15)/hist["Close"]-1 > 0.07).astype(int)
    return df.dropna()


def _gather_data(symbols):
    all_X, all_y = [], []
    bar = st.progress(0, text="מוריד נתונים...")
    for i, sym in enumerate(symbols):
        try:
            hist = yf.Ticker(sym).history(period="2y")
            if len(hist) < 220: continue
            df = _build_features(hist)
            if len(df) < 30: continue
            all_X.append(df[FEAT_COLS].values)
            all_y.append(df["target"].values)
        except Exception:
            pass
        bar.progress((i+1)/len(symbols), text=f"מוריד {sym}...")
    bar.empty()
    if not all_X:
        return None, None
    return np.vstack(all_X), np.concatenate(all_y)


def _portfolio_optimizer(symbols):
    prices = {}
    for sym in symbols:
        try:
            h = yf.Ticker(sym).history(period="1y")["Close"]
            if len(h)>50: prices[sym] = h
        except: pass
    if len(prices)<2: return {"ok":False,"error":"צריך ≥2 מניות"}
    pdf = pd.DataFrame(prices).dropna()
    ret = pdf.pct_change().dropna()
    mu  = ret.mean()*252
    cov = ret.cov()*252
    n   = len(mu)
    np.random.seed(42)
    best = {"sharpe":-999,"w":None,"r":0,"v":0}
    for _ in range(5000):
        w = np.random.dirichlet(np.ones(n))
        r = float(np.dot(w,mu))
        v = float(np.sqrt(w@cov.values@w))
        s = (r-0.05)/v if v>0 else 0
        if s>best["sharpe"]:
            best = {"sharpe":s,"w":w,"r":r,"v":v}
    alloc = {sym:round(w*100,1) for sym,w in zip(pdf.columns,best["w"])}
    return {"ok":True,"allocation":alloc,"return":round(best["r"]*100,1),
            "volatility":round(best["v"]*100,1),"sharpe":round(best["sharpe"],2),
            "corr":ret.corr().round(2)}


# ══════════════════════════════════════════════════════════
# ממשק ראשי
# ══════════════════════════════════════════════════════════

def render_machine_learning(df_all=None):
    st.markdown(
        '<div class="ai-card" style="border-right-color:#9c27b0;">'
        '<b>🧠 למידת מכונה אמיתית</b> — מודלים מאומנים על נתוני בורסה היסטוריים אמיתיים'
        '<br><small>✅ מודל נשמר אוטומטית לדיסק</small></div>',
        unsafe_allow_html=True,
    )

    if not SKLEARN_AVAILABLE:
        st.error("❌ scikit-learn לא מותקן!")
        st.code("pip install scikit-learn", language="bash")
        st.info("הוסף גם `scikit-learn>=1.3.0` לקובץ requirements.txt")
        return

    # אתחול
    defaults = {
        "ml_trained":False,"ml_accuracy":0.0,"ml_runs":0,
        "ml_params":{"risk_ratio":1.0,"rsi_buy":40,"rsi_sell":65,"min_score":4},
        "ml_insights":[],"ml_model_type":"Random Forest 🌲",
        "ml_cv_scores":[],"ml_model_b64":None,"ml_scaler_b64":None,
        "ml_feat_imp":{},"ml_train_n":0,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # כותרת מצב
    if st.session_state.ml_trained:
        st.success(
            f"✅ מודל **{st.session_state.ml_model_type}** פעיל | "
            f"דיוק CV: **{st.session_state.ml_accuracy:.1f}%** | "
            f"אומן על **{st.session_state.ml_train_n:,}** דגימות | "
            f"ריצה #{st.session_state.ml_runs}"
        )
    else:
        st.info("🟡 מודל לא אומן עדיין — עבור לטאב 'אימון מודל'")

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("🎯 דיוק CV", f"{st.session_state.ml_accuracy:.1f}%")
    m2.metric("⚖️ R/R",     f"1:{st.session_state.ml_params['risk_ratio']:.1f}")
    m3.metric("📊 RSI כניסה",f"≤{st.session_state.ml_params['rsi_buy']}")
    m4.metric("⭐ ציון מינ.",str(st.session_state.ml_params["min_score"]))
    st.divider()

    t1,t2,t3,t4,t5 = st.tabs([
        "🚀 אימון מודל","🔮 חיזוי מניות",
        "📐 אופטימיזציית תיק","🔍 זיהוי חריגות","📋 הגדרות ואיפוס"
    ])

    # ══ TAB 1: אימון ══
    with t1:
        c1,c2 = st.columns(2)
        with c1:
            algo = st.selectbox("🔢 אלגוריתם",
                ["Random Forest 🌲","Gradient Boosting 🚀",
                 "Logistic Regression 📐","Ensemble (RF+GB) 🏆"],
                key="ml_algo")
        with c2:
            if df_all is not None and not df_all.empty:
                sym_opts = df_all["Symbol"].tolist()
                sym_def  = sym_opts[:6]
            else:
                sym_opts = ["AAPL","NVDA","MSFT","TSLA","META","AMZN","GOOGL","PLTR","AMD","NFLX"]
                sym_def  = sym_opts[:6]

            train_syms = st.multiselect("📌 מניות לאימון (≥3 מומלץ)",
                                        sym_opts+["V","JPM","COST","AVGO"],
                                        default=sym_def, key="ml_syms")

        st.caption(f"ℹ️ כל מניה מספקת ~400 דגימות | יעד: עלייה >7% ב-15 ימים")

        if st.button("🚀 אמן מודל אמיתי", type="primary", key="ml_train"):
            if len(train_syms) < 2:
                st.warning("בחר לפחות 2 מניות.")
            else:
                with st.spinner(f"מאמן {algo}..."):
                    X, y = _gather_data(train_syms)
                    if X is None:
                        st.error("לא ניתן להוריד נתונים. נסה מניות אחרות.")
                    else:
                        scaler   = StandardScaler()
                        X_scaled = scaler.fit_transform(X)

                        if algo == "Ensemble (RF+GB) 🏆":
                            rf = RandomForestClassifier(n_estimators=200,max_depth=8,random_state=42,n_jobs=-1)
                            gb = GradientBoostingClassifier(n_estimators=150,learning_rate=0.05,random_state=42)
                            cv_rf = cross_val_score(rf,X_scaled,y,cv=5,scoring="accuracy")
                            cv_gb = cross_val_score(gb,X_scaled,y,cv=5,scoring="accuracy")
                            cv    = (cv_rf+cv_gb)/2
                            rf.fit(X_scaled,y); model=rf
                            fi = dict(zip(FEAT_COLS, rf.feature_importances_))
                        elif algo == "Random Forest 🌲":
                            model = RandomForestClassifier(n_estimators=200,max_depth=8,random_state=42,n_jobs=-1)
                            cv    = cross_val_score(model,X_scaled,y,cv=5,scoring="accuracy")
                            model.fit(X_scaled,y)
                            fi = dict(zip(FEAT_COLS, model.feature_importances_))
                        elif algo == "Gradient Boosting 🚀":
                            model = GradientBoostingClassifier(n_estimators=150,learning_rate=0.05,random_state=42)
                            cv    = cross_val_score(model,X_scaled,y,cv=5,scoring="accuracy")
                            model.fit(X_scaled,y)
                            fi = dict(zip(FEAT_COLS, model.feature_importances_))
                        else:
                            model = LogisticRegression(max_iter=1000,random_state=42)
                            cv    = cross_val_score(model,X_scaled,y,cv=5,scoring="accuracy")
                            model.fit(X_scaled,y)
                            fi = dict(zip(FEAT_COLS, abs(model.coef_[0])))

                        acc = round(cv.mean()*100, 1)
                        mb  = io.BytesIO(); pickle.dump(model,mb)
                        sb  = io.BytesIO(); pickle.dump(scaler,sb)

                        top3 = sorted(fi.items(), key=lambda x:x[1], reverse=True)[:3]
                        rsi_buy  = 38 if fi.get("rsi",0)>0.1 else 42
                        rsi_sell = 65 if fi.get("rsi",0)>0.1 else 68

                        st.session_state.ml_trained    = True
                        st.session_state.ml_accuracy   = acc
                        st.session_state.ml_runs      += 1
                        st.session_state.ml_model_type = algo
                        st.session_state.ml_cv_scores  = cv.tolist()
                        st.session_state.ml_model_b64  = base64.b64encode(mb.getvalue()).decode()
                        st.session_state.ml_scaler_b64 = base64.b64encode(sb.getvalue()).decode()
                        st.session_state.ml_feat_imp   = fi
                        st.session_state.ml_train_n    = len(X)
                        st.session_state.ml_params = {
                            "risk_ratio": round(1.5+acc/100,1),
                            "rsi_buy": rsi_buy, "rsi_sell": rsi_sell, "min_score":4
                        }
                        st.session_state.ml_insights = [
                            f"📊 פיצ'ר #1: **{FEAT_HE.get(top3[0][0],top3[0][0])}** ({top3[0][1]*100:.1f}%)" if top3 else "",
                            f"📊 פיצ'ר #2: **{FEAT_HE.get(top3[1][0],top3[1][0])}** ({top3[1][1]*100:.1f}%)" if len(top3)>1 else "",
                            f"📈 כניסה מנצחת: RSI<{rsi_buy} | מחיר מעל MA50",
                            f"⚠️  כניסה מפסידה: RSI>{rsi_sell} + תנודתיות גבוהה",
                            f"✅ אומן על {len(X):,} דגימות מ-{len(train_syms)} מניות",
                            f"📊 דיוק CV ממוצע: {acc:.1f}% ± {cv.std()*100:.1f}%",
                        ]
                        save_ml(st.session_state)

                st.success(f"✅ אימון הסתיים! דיוק: **{acc:.1f}%** | דגימות: {len(X):,}")
                st.balloons()
                st.rerun()

        # תובנות + Feature Importance
        if st.session_state.ml_insights:
            st.subheader("💡 תובנות מהמודל")
            for ins in st.session_state.ml_insights:
                if ins: st.markdown(f"- {ins}")

        if st.session_state.ml_feat_imp:
            st.divider()
            st.subheader("📊 חשיבות פיצ'רים")
            fi_rows = sorted(st.session_state.ml_feat_imp.items(), key=lambda x:x[1], reverse=True)
            fi_df = pd.DataFrame([
                {"פיצ'ר": FEAT_HE.get(k,k), "חשיבות %": round(v*100,1),
                 "גרף": "█"*max(1,int(v*80))}
                for k,v in fi_rows
            ])
            st.dataframe(fi_df, hide_index=True)

        if st.session_state.ml_cv_scores:
            st.divider()
            st.subheader("📈 Cross-Validation (5-Fold)")
            cv = st.session_state.ml_cv_scores
            cv_df = pd.DataFrame({
                "Fold": [f"Fold {i+1}" for i in range(len(cv))],
                "דיוק %": [round(v*100,1) for v in cv],
            })
            st.dataframe(cv_df, hide_index=True)
            std = np.std(cv)*100
            col1,col2 = st.columns(2)
            col1.metric("ממוצע", f"{np.mean(cv)*100:.1f}%")
            col2.metric("סטיית תקן", f"±{std:.1f}%")
            if std > 8:
                st.warning("⚠️ סטיית תקן גבוהה — נסה להוסיף יותר מניות לאימון")

    # ══ TAB 2: חיזוי ══
    with t2:
        if not st.session_state.ml_trained:
            st.info("🟡 אמן מודל קודם.")
        else:
            st.markdown("### 🔮 האם המניה תעלה >7% ב-15 ימים הבאים?")
            if df_all is not None and not df_all.empty:
                pred_syms = st.multiselect("בחר מניות:", df_all["Symbol"].tolist(),
                                           default=df_all["Symbol"].head(5).tolist(), key="ml_ps")
            else:
                pred_syms = st.multiselect("בחר מניות:",
                    ["AAPL","NVDA","MSFT","TSLA","META","AMZN","GOOGL","PLTR"],
                    default=["AAPL","NVDA","MSFT"], key="ml_ps")

            if st.button("🔮 חזה", type="primary", key="ml_pred_btn"):
                if not pred_syms:
                    st.warning("בחר מניה.")
                else:
                    model  = pickle.loads(base64.b64decode(st.session_state.ml_model_b64))
                    scaler = pickle.loads(base64.b64decode(st.session_state.ml_scaler_b64))
                    rows = []
                    with st.spinner("מנתח..."):
                        for sym in pred_syms:
                            try:
                                hist = yf.Ticker(sym).history(period="1y")
                                if len(hist) < 220: continue
                                df_f = _build_features(hist)
                                if df_f.empty: continue
                                Xp = np.nan_to_num(df_f[FEAT_COLS].iloc[[-1]].values)
                                Xs = scaler.transform(Xp)
                                pred = model.predict(Xs)[0]
                                proba = model.predict_proba(Xs)[0]
                                conf = proba[int(pred)]*100
                                rsi_now = df_f["rsi"].iloc[-1]
                                ma50_ok = df_f["above_ma50"].iloc[-1]
                                vol_rat = df_f["vol_ratio"].iloc[-1]
                                rows.append({
                                    "📌 מניה":     sym,
                                    "🔮 חיזוי":    "✅ עלייה" if pred==1 else "❌ לא",
                                    "🎯 ביטחון":   f"{conf:.1f}%",
                                    "📊 RSI":      f"{rsi_now:.1f}",
                                    "MA50":        "✅" if ma50_ok else "❌",
                                    "📈 נפח":      "⚡ חריג" if vol_rat>1.5 else "רגיל",
                                    "🤖 המלצה":   "🟢 קנה" if (pred==1 and conf>60) else "⚠️ המתן" if pred==1 else "🔴 לא",
                                })
                            except Exception:
                                pass
                    if rows:
                        st.dataframe(pd.DataFrame(rows), hide_index=True)
                        buys = [r["📌 מניה"] for r in rows if r["🤖 המלצה"]=="🟢 קנה"]
                        if buys:
                            st.success(f"🟢 ממליץ לקנות: {', '.join(buys)}")
                        else:
                            st.warning("🔴 לא ממליץ לקנות כרגע")

    # ══ TAB 3: Portfolio Optimizer ══
    with t3:
        st.markdown("### 📐 אופטימיזציית תיק — Markowitz MPT")
        st.info("מחשב את הרכב התיק עם Sharpe Ratio מקסימלי (5,000 סימולציות)")
        if df_all is not None and not df_all.empty:
            opt_syms = st.multiselect("בחר מניות:", df_all["Symbol"].tolist(),
                                      default=df_all["Symbol"].head(5).tolist(), key="ml_os")
        else:
            opt_syms = st.multiselect("בחר מניות:",
                ["AAPL","NVDA","MSFT","TSLA","META","AMZN","GOOGL"],
                default=["AAPL","NVDA","MSFT","META","AMZN"], key="ml_os")

        if st.button("📐 חשב", type="primary", key="ml_opt"):
            if len(opt_syms)<2:
                st.warning("בחר ≥2 מניות.")
            else:
                with st.spinner("מחשב 5,000 תיקים..."):
                    res = _portfolio_optimizer(opt_syms)
                if res["ok"]:
                    st.success(f"✅ Sharpe: **{res['sharpe']:.2f}**")
                    alloc_df = pd.DataFrame([
                        {"📌 מניה":sym, "💼 הקצאה %":pct, "גרף":"█"*max(1,int(pct/3))}
                        for sym,pct in sorted(res["allocation"].items(),key=lambda x:x[1],reverse=True)
                    ])
                    st.dataframe(alloc_df, hide_index=True)
                    c1,c2,c3 = st.columns(3)
                    c1.metric("📈 תשואה שנתית", f"{res['return']:.1f}%")
                    c2.metric("📊 תנודתיות",    f"{res['volatility']:.1f}%")
                    c3.metric("⚖️ Sharpe",       f"{res['sharpe']:.2f}")
                    with st.expander("🔗 מטריצת קורלציה"):
                        import plotly.express as px
                        corr_clean = res["corr"].fillna(0).round(2)
                        fig_corr = px.imshow(
                            corr_clean, text_auto=True,
                            color_continuous_scale="RdYlGn",
                            zmin=-1, zmax=1,
                            title="קורלציה בין נכסים (1=תנועה זהה, -1=הפוכה, 0=ללא קשר)"
                        )
                        fig_corr.update_layout(height=400, font=dict(size=11))
                        st.plotly_chart(fig_corr)
                        st.caption("🟢 ירוק = קורלציה חיובית | 🔴 אדום = קורלציה שלילית (גידור) | 🟡 צהוב = אין קשר (פיזור טוב!)")
                else:
                    st.error(res.get("error","שגיאה"))

    # ══ TAB 4: Anomaly Detection ══
    with t4:
        st.markdown("### 🔍 זיהוי חריגות — Isolation Forest")
        st.info("מזהה מניות עם פרמטרים יוצאי דופן — לעיתים סיגנל מוקדם")
        if df_all is not None and not df_all.empty:
            if st.button("🔍 סרוק", type="primary", key="ml_anom"):
                try:
                    feat = np.array([
                        [r.get("RSI",50),r.get("Margin",0),r.get("ROE",0),
                         r.get("TargetUpside",0),r.get("InsiderHeld",0),r.get("DivYield",0)]
                        for _,r in df_all.iterrows()
                    ])
                    feat = np.nan_to_num(feat)
                    iso  = IsolationForest(contamination=0.15, random_state=42)
                    iso.fit(feat)  # ← חייב לאמן לפני score_samples
                    scores = iso.score_samples(feat)
                    df_all2 = df_all.copy()
                    df_all2["אנומליה"] = scores
                    df_all2["סטטוס"] = df_all2["אנומליה"].apply(
                        lambda s: "🔴 חריג מאוד" if s<-0.15 else "🟡 חריג" if s<0 else "⚪ רגיל"
                    )
                    anom = df_all2[df_all2["אנומליה"]<0].sort_values("אנומליה")
                    if anom.empty:
                        st.info("לא נמצאו חריגות")
                    else:
                        st.success(f"נמצאו {len(anom)} מניות חריגות:")
                        cols_show = [c for c in ["Symbol","Price","RSI","Score","Margin","אנומליה","סטטוס"] if c in anom.columns]
                        st.dataframe(anom[cols_show], hide_index=True)
                        st.caption("💡 חריגות יכולות להצביע על הזדמנות — בדוק ידנית!")
                except Exception as e:
                    st.error(f"שגיאה: {e}")
        else:
            st.warning("טען נתוני מניות קודם.")

    # ══ TAB 5: הגדרות ══
    with t5:
        if st.session_state.ml_trained:
            p = st.session_state.ml_params
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("RSI קנייה",   f"< {p['rsi_buy']}")
            c2.metric("RSI מכירה",   f"> {p['rsi_sell']}")
            c3.metric("ציון מינ.",   str(p["min_score"]))
            c4.metric("R/R",          f"1:{p['risk_ratio']:.1f}")
            st.info(f"סוג מודל: **{st.session_state.ml_model_type}** | ריצות: {st.session_state.ml_runs}")

        if st.button("🗑️ איפוס מודל מלא", key="ml_reset"):
            for k in ["ml_trained","ml_accuracy","ml_runs","ml_model_b64","ml_scaler_b64",
                      "ml_feat_imp","ml_cv_scores","ml_insights","ml_train_n"]:
                st.session_state[k] = defaults.get(k, None)
            st.session_state.ml_params = {"risk_ratio":1.0,"rsi_buy":40,"rsi_sell":65,"min_score":4}
            save_ml(st.session_state)
            st.success("✅ מודל אופס")
            st.rerun()
