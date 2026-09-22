import pandas as pd


def calculate_smartscore(row):
    """
    Tính SmartScore từ 0 đến 100.

    SmartScore chỉ dùng để đánh giá chất lượng tương đối
    của cổ phiếu, không thay đổi tín hiệu MUA/BÁN.
    """

    score = 0

    # =====================================================
    # 1. RELATIVE STRENGTH - 30 ĐIỂM
    # =====================================================

    rs = row.get("RS")

    if pd.notna(rs):

        rs_score = min(
            max(float(rs), 0),
            100
        ) * 0.30

        score += rs_score

    # =====================================================
    # 2. EMA20 > EMA50 - 20 ĐIỂM
    # =====================================================

    if bool(row.get("EMA_ok", False)):

        score += 20

    # =====================================================
    # 3. GIÁ > SMA200 - 15 ĐIỂM
    # =====================================================

    if bool(row.get("SMA200_ok", False)):

        score += 15

    # =====================================================
    # 4. THANH KHOẢN - 15 ĐIỂM
    # =====================================================

    if bool(row.get("Liquidity_ok", False)):

        score += 15

    # =====================================================
    # 5. ADX - 10 ĐIỂM
    # =====================================================

    adx = row.get("ADX14")

    if pd.notna(adx):

        if adx >= 25:

            score += 10

        elif adx >= 20:

            score += 5

    # =====================================================
    # 6. ANTI-CHASING - 5 ĐIỂM
    # =====================================================

    if bool(row.get("AntiChasing_ok", False)):

        score += 5

    # =====================================================
    # 7. GẦN ĐỈNH 252 PHIÊN - 5 ĐIỂM
    # =====================================================

    if bool(row.get("PriceNearHigh_ok", False)):

        score += 5

    # =====================================================
    # GIỚI HẠN 0-100
    # =====================================================

    score = max(
        0,
        min(score, 100)
    )

    return round(score, 1)


def add_smartscore(df):

    if df is None or df.empty:

        return pd.DataFrame()

    df = df.copy()

    df["SmartScore"] = df.apply(
        calculate_smartscore,
        axis=1
    )

    return df