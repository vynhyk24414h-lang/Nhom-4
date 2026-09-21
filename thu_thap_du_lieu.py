import requests
import pandas as pd
import json
import sys

# Fix lỗi font tiếng Việt khi in ra Terminal trên Windows
sys.stdout.reconfigure(encoding='utf-8')

# Khai báo các hằng số và header cần thiết để gọi API Fireant
# Các thông tin Header này giúp định danh trình duyệt và vượt qua kiểm tra tường lửa
HEADERS = {
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    # TODO: Bạn BẮT BUỘC phải dán chuỗi cookie lấy từ trình duyệt (F12 -> Network) vào đây để API không báo lỗi 401/403
    "Cookie": "FireAnt.Authentication.v3=-t1DmlRbT0Zar-JxK11YxMh52Pe3SndgBifci_sWsxnvxJSVrPwxUmo_Zr1DBHWFAHmECaNlmgVn9dDn21ONctBYmzki2xBySLqxxPYWPyPZMLDmQScLPdkyWve4pgR_-87szkLB0iMQCD7OikIaZ3aIej-daA7cNS4xU5FQtZQYpHy_CsdbMVl1PySvgwTLPOpfz-3JS3TVlvbS4hIfevBoRwgxsZ0SMQmRtzKCKbJzQmOFHETOvZPK-SX3GANdkU7pb2BpE1Cna48OKkwgZh7glPUAOL9CtHgHLpjUE3xeWrHS1hw17XXHrmNzPtG6VM-yexIL7s3P4WFh6cekJZR9T9K2LRXsnly54mCSmW25XI-VOKIp4m1hkC-No_VlXc13TaClkqHr1Y4Q8RcgSEVBsm42SMpqC_oCgrp5nAiqCAG8m_D56jbe63SD6iNTvDABpZYKZBqtHMZghTQnt1mYXvvNIoPRZ7JO1EKN0W_x6d4b6w8thj6o3SXh6lvlGOBilcVxnrO8BFJ2ml9o_i18cZkXkjVFhjsqCZnZcIXvGAdXoC5ISleNfoJONmqReCVT7ecmmNx9KjJjHhzc2m_G8HhbR1ggcrRNItQuyuyKYtkl3giG5m4Dr8h0TLYnPDrYnWFCjmiBguEo_2lfRJ0lZqe5zvAOPn_t3ZaPe9KIU1dzrXcNFUiLtwFvuXFpBkG79bGJwmSe7CuoMPQRT2pR_sPv6e1lPasXmedLc_irq3Gju9igxvk2AhYs3w_pQUCz9LnbUrJF2teRbu7suSCdGZuM6zPzx0D8loBXLsLGTewNKWyxk4rRFHZNaXvtPwPhGCueMIigACAwa1bZ4bvongkCAENlvPus5asQK9-o_Pf7CNf32NBtP1ormHy9m1XfQcQzA1QjEhBqTG70VUy9NLUUkR5tcZUA6rsrfSf885gUYH7cUZIeUJoFRa_8xwVbu3Ggm5clYQLUo8nR_g8QacjNgph_9lnh6jXp4T8GJ5VHTom1DURmJWoIhX_E2fRGQhtunZOApFPr3sclKqfupIkTuoMXZPlhQxkafSkdH2cpoSpTtvjGMOshBL1zez870ccgXc6WAtA8hlKeWTTMvZLlw0oU1buYweqr9h5vwPk0Rk41nUQzuV__phJOCQUzS__GpMHxGWEUdFwZ2WMT25SUYJs-hnP1cZvvqnyNUpcIJTINz_RSkg9ziEeJIGeOk50yq0I6Iz48-pRSDMwqybMlf0WEL55FEK9wTqKy6UEeAA7M0tilLUEpBfFr9aGVtm1LkGGhPrWoUjx9Y63I2iIOfeDx9VWk1gkvA_rVkIqjaXWOsyfu2hVAf3pTWnshZ71hc_6Jt5emwsfA8fZA9Fv_-PclCvXcoFhWIH-GUb0jcLRgrVeBWf4QvDKacrBZMvD2fGj86JdTGOxCU0ziR74NmSRzaJC4IKW3zA87onuvmfHFjBmSOuHMCxWlfOpnQRQE_qgDcDpz6WHvnYSCmX_9StFzQZSjUkDyTtDyBjnNvKHY7nbLh95YlcMIPAIyp2xv9w-Yqhu96g_RnUPgVB_55Bkk4MpTQ6SzMNRgd9GgeYV-oTX-GlazRwQRX9EzZZctVw7J7fAprJb1i0ikVX5j791jafwmvuPsNbMmetzpTEwMkMfA08MRudL7U25vOzw01Vd5UWZR3sb1V_4EM8B3nyaBVI4N4sciVkapFTMNEaYsQKnN0cPof2xnikBoXIpVSxb3mZWj3_voFFZGvPV5_6dn2GddBl8S_bdw9jtMR_o6epJK7lm2vhXb6PDFN_W6M5vXiQSz8DfRAkIoqrnYMK-bK3txgEI9-a1o1ka7-VDvT_flCtL-_XZb_qNmLZEXDTMK5JtLsfqt1hVHlqpZgjR4F7A6N0iOjA6s_VjqHNnJbh7fz1pQP-Sg0ft6B6tPyD15WWY8VDQ9rlFzS-hsKCax4ggINcJxPJvY0u9uanBWBK8gKdV9YTX8wswXJ0x78u9Gdrl9YPpZ82dNLTsMR5bZbsw5BALwmKabmy-5hmU7d9Ev0cx_lczsmZBG8666DmBbPMxUgxe4umice2nXWel2JhOxi-KxJFxsF4_eQQJSZixWyjYw0TuFsh395pYbRXltD5iyl4C_FiaUdVzY0FNpEY-rl-Jz-iWE2V8ns5NrVA51ABN0R1mg9QIP1MgmDxnetGedXSVI9WWdJJPA0Q_k4hikm7_dhi2wj8hhE0jIFjtxfUiC0xJBXVq4wPAOc_zcRmHcNu0CVrYEW1Mb85bK1cgnI_MQZZ7AhODAZqh4zpFK4xqEwg65VDElQGTBoQJhq6z-KGAdEpk4p9ebMTRRUi2_1RyHk3XdZdY3snpte5oaRCzbjSVBigNe5yKpbxd5JtGmLJuYJZJrOWnSzrdkKeEN4aq4BTI_xyN5pVlPGkBxaYj0273nxucLk1ttkSqUX9YloG_YZAj24ySfw4ohFPZmYvArjv52Y8vUG1cNV9aty7nAflGV0h9FDhFPQUKJ533iRiMacBjvTFsfZ3HV9uVS7n6xDXe470bXpg0zp_vz5bfVZWf18oGvKq7yF950KGsKK-z-P8vU40Xilvq0Io2_meFyLYNDbxN1WUOfSVVJD38gC__KhC4f6XJKaQDKNNSAjpu4YV2w2fa3pIFyAxISKyGXUeBcP9pCUZzW7mDAVdfjQb_xtOLsBjLiKGPDc29xBK8GoTus5dSQm80FbdU7_uQWMGb-9qJlkhq7UfhDL1ystVUXzL9YR1GTQ7_4rj-aHCnDtvjeOOkOaq9Dxu6XOC4ucNsZKb6IDg1RK07MwbHqQpq-F8LyJ9FYHvFUWUT5TY5Mj0ztJRpS8I8jjRdC8J7X4mDfFX4YK3NOb2SxKLUyQlvb1alJTMBpZCtI2YWoLUM7h_FIvrqMsOnd1YGLWjP8Ae0wjqvFXhPysOwoA9Hwo8sgzCntT-vvVkCzbPbITBtUkUA5Rwt_N_LfpoXiM2DNuyb7qQXXxudYvJhgMLZ11an_ii70XhLfND7Ig7F9ylaSbhjzz_o; _ga_YC91R5F249=GS2.1.s1789983426$o142$g1$t1789984105$j55$l0$h0$dFaTuOOJjO8iSHmFujNoSJNNjNiRKEtLNVw; _gid=GA1.2.977338454.1789984111; _gat=1; ASP.NET_SessionId=u4gyaeskjwuckcfkic12kf05; _ga_ZJ4G3SW582=GS2.1.s1789983426$o143$g1$t1789984148$j9$l0$h0$d7zgJJPB5GSGBRcPkimLvfNXmNHZmLP1rkQ; _ga=GA1.2.1585411280.1786081407"
}

# Hàm 1: Lấy danh sách mã cổ phiếu và thống kê giao dịch
def get_trading_statistics():
    # Đường dẫn API lấy danh sách cổ phiếu từ bảng thống kê của Fireant
    url = "https://www.fireant.vn/api/Data/Markets/TradingStatistic"
    print(f"[*] Đang lấy danh sách mã cổ phiếu từ {url}")
    
    # Gửi yêu cầu HTTP GET kèm theo headers để vượt qua tường lửa
    response = requests.get(url, headers=HEADERS)
    
    # Kiểm tra mã trạng thái HTTP trả về
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[!] Lỗi khi lấy danh sách mã cổ phiếu. Mã lỗi: {response.status_code}")
        return None

# Hàm 2: Lấy dữ liệu giao dịch trong ngày (Realtime - thời gian thực)
def get_realtime_data(symbol):
    # Đường dẫn API lấy dữ liệu realtime
    url = f"https://www.fireant.vn/api/Data/Markets/IntradayQuotes?symbol={symbol}"
    print(f"[*] Đang lấy dữ liệu realtime cho mã: {symbol}")
    
    # Gửi yêu cầu HTTP GET
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[!] Lỗi khi lấy dữ liệu realtime mã {symbol}. Mã lỗi: {response.status_code}")
        return None

# Hàm 3: Lấy dữ liệu giao dịch lịch sử (History)
def get_historical_data(symbol, start_date, end_date):
    # Đường dẫn API lấy dữ liệu lịch sử
    url = f"https://www.fireant.vn/api/Data/Markets/HistoricalQuotes?symbol={symbol}&startDate={start_date}&endDate={end_date}"
    print(f"[*] Đang lấy dữ liệu lịch sử cho mã: {symbol} từ {start_date} đến {end_date}")
    
    # Gửi yêu cầu HTTP GET
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[!] Lỗi khi lấy dữ liệu lịch sử mã {symbol}. Mã lỗi: {response.status_code}")
        return None

# Khối lệnh chính để chạy script
if __name__ == "__main__":
    
    # --- 1. LẤY DANH SÁCH MÃ CỔ PHIẾU ---
    stats_data = get_trading_statistics()
    
    if stats_data:
        # Tạo danh sách chứa các mã cổ phiếu
        danh_sach_ma = []
        for item in stats_data:
            if 'symbol' in item:
                danh_sach_ma.append(item['symbol'])
            elif 'Symbol' in item:
                danh_sach_ma.append(item['Symbol'])
                
        if danh_sach_ma:
            print(f"[+] Lấy thành công {len(danh_sach_ma)} mã cổ phiếu.")
            df_symbols = pd.DataFrame(danh_sach_ma, columns=["MaCoPhieu"])
            file_out = "DanhSachMaCoPhieu.csv"
            df_symbols.to_csv(file_out, index=False)
            print(f"[*] Đã xuất danh sách mã ra file: {file_out}\n")
    
    # ==============================================================================
    # LƯU Ý CHO GIAI ĐOẠN SAU:
    # Ở giai đoạn tiếp theo, các bạn trong nhóm chỉ cần đọc file DanhSachMaCoPhieu.csv
    # và chạy vòng lặp (For loop) gọi 2 hàm get_realtime_data() và get_historical_data()
    # được định nghĩa ở trên để tải toàn bộ dữ liệu.
    # ==============================================================================
    
    print("[+] KẾT THÚC CHƯƠNG TRÌNH.")
