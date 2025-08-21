import streamlit as st
import ldap3
import os
from ldap_config import LDAP_CONFIG

def ldap_authenticate(username, password):
    """
    LDAP sunucusunda kullanıcı kimlik doğrulaması yapar (ldap3 ile SSL sertifika desteği)
    """
    try:
        # LDAP sunucu bilgilerini al
        server_url = LDAP_CONFIG["server"]
        base_dn = LDAP_CONFIG.get("user_base_dn", LDAP_CONFIG["base_dn"])
        bind_dn = LDAP_CONFIG["bind_dn"]
        bind_password = LDAP_CONFIG["bind_password"]
        
        # SSL ayarlarını yapılandır
        use_ssl = server_url.startswith('ldaps://')
        use_tls = server_url.startswith('ldap://') and LDAP_CONFIG.get("ssl_verify", True)
        
        # Server oluştur
        if use_ssl:
            # SSL ile bağlantı - basit yaklaşım
            try:
                # SSL sertifika varsa kullan, yoksa basit SSL
                if LDAP_CONFIG.get("ssl_certificate") and os.path.exists(LDAP_CONFIG.get("ssl_certificate")):
                    server = ldap3.Server(
                        server_url.replace('ldaps://', '').split(':')[0],
                        port=int(server_url.split(':')[-1]),
                        use_ssl=True,
                        tls=ldap3.Tls(
                            ca_certs_file=LDAP_CONFIG.get("ssl_certificate")
                        )
                    )
                else:
                    # Sertifika yoksa basit SSL
                    server = ldap3.Server(
                        server_url.replace('ldaps://', '').split(':')[0],
                        port=int(server_url.split(':')[-1]),
                        use_ssl=True
                    )
            except Exception as e:
                # Herhangi bir hata durumunda basit SSL kullan
                server = ldap3.Server(
                    server_url.replace('ldaps://', '').split(':')[0],
                    port=int(server_url.split(':')[-1]),
                    use_ssl=True
                )
        else:
            # Normal bağlantı
            server = ldap3.Server(
                server_url.replace('ldap://', '').split(':')[0],
                port=int(server_url.split(':')[-1]),
                use_ssl=False
            )
        
        # Admin olarak bağlan
        admin_conn = ldap3.Connection(
            server,
            user=bind_dn,
            password=bind_password,
            auto_bind=True
        )
        
        if not admin_conn.bound:
            return False, f"Admin bağlantısı başarısız: {admin_conn.result}"
        
        # Kullanıcıyı ara
        user_filter = f"({LDAP_CONFIG['user_filter_attribute']}={username})"
        admin_conn.search(
            search_base=base_dn,
            search_filter=user_filter,
            search_scope=ldap3.SUBTREE,
            attributes=[ldap3.ALL_ATTRIBUTES]
        )
        
        if not admin_conn.entries:
            admin_conn.unbind()
            return False, "Kullanıcı bulunamadı"
        
        user_dn = admin_conn.entries[0].entry_dn
        
        # Kullanıcı şifresi ile bağlanmayı dene
        user_conn = ldap3.Connection(
            server,
            user=user_dn,
            password=password,
            auto_bind=True
        )
        
        if not user_conn.bound:
            admin_conn.unbind()
            return False, "Geçersiz kullanıcı adı veya şifre"
        
        # Grup kontrolü
        if LDAP_CONFIG.get("group_auth_pattern"):
            # Pattern'deki ${USER} placeholder'ını gerçek kullanıcı adı ile değiştir
            group_filter = LDAP_CONFIG["group_auth_pattern"].replace("${USER}", username)
            
            # Kullanıcının base DN'inde grup kontrolü yap
            user_conn.search(
                search_base=base_dn,
                search_filter=group_filter,
                search_scope=ldap3.SUBTREE,
                attributes=[ldap3.ALL_ATTRIBUTES]
            )
            
            group_found = len(user_conn.entries) > 0
        else:
            # Eski yöntem (fallback) - kullanıcının memberOf attribute'unu kontrol et
            user_conn.search(
                search_base=user_dn,
                search_filter="(objectClass=user)",
                search_scope=ldap3.BASE,
                attributes=[LDAP_CONFIG.get("group_member_attribute", "memberOf")]
            )
            
            if user_conn.entries:
                user_attrs = user_conn.entries[0]
                group_attr = LDAP_CONFIG.get("group_member_attribute", "memberOf")
                
                if hasattr(user_attrs, group_attr):
                    group_values = getattr(user_attrs, group_attr)
                    if isinstance(group_values, list):
                        group_found = any(LDAP_CONFIG["group_dn"] in group_value for group_value in group_values)
                    else:
                        group_found = LDAP_CONFIG["group_dn"] in str(group_values)
                else:
                    group_found = False
            else:
                group_found = False
        
        # Bağlantıları kapat
        admin_conn.unbind()
        user_conn.unbind()
        
        if group_found:
            return True, "Kullanıcı doğrulandı ve grupta bulundu"
        else:
            return False, "Kullanıcı doğrulandı ancak gerekli grupta değil"
            
    except ldap3.core.exceptions.LDAPBindError as e:
        return False, f"LDAP bağlantı hatası: {str(e)}"
    except ldap3.core.exceptions.LDAPException as e:
        return False, f"LDAP hatası: {str(e)}"
    except Exception as e:
        return False, f"Genel hata: {str(e)}"

# Sayfa yapılandırması
st.set_page_config(page_title="ING - DDP", page_icon="🔐", layout="centered", initial_sidebar_state="expanded")

# Kullanıcı veritabanı ve onaylayıcı ilişkileri
USERS = {
    "okan": {
        "password": "123456",
        "name": "Okan",
        "approver": "emir"  # Okan'ın onaylayıcısı Emir
    },
    "emir": {
        "password": "654321", 
        "name": "Emir",
        "approver": "okan"  # Emir'in onaylayıcısı Okan (örnek)
    }
}

# Session state kontrolü
if 'show_sms' not in st.session_state:
    st.session_state.show_sms = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'anasayfa'
if 'username' not in st.session_state:
    st.session_state.username = None
if 'pending_uploads' not in st.session_state:
    st.session_state.pending_uploads = []
if 'history' not in st.session_state:
    st.session_state.history = []

# URL parametreleri ile session kontrolü - güvenlik için kaldırıldı
# Artık sadece gerçek login işlemleri session state'i güncelleyebilir
# Bu sayede logout sonrası URL manipülasyonu engellenmiş oldu

# Genel stil ayarları
st.markdown("""
    <style>
    /* Genel ayarlar */
    .stApp {
        background-color: white;
    }
    /* Dashboard yazı rengi */
    .main .stMarkdown {
        color: black !important;
    }
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: black !important;
    }
    .main p {
        color: black !important;
    }
    /* Streamlit başlık ve metin renkleri */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: black !important;
    }
    .stMarkdown p {
        color: black !important;
    }
    div[data-testid="stMarkdownContainer"] {
        color: black !important;
    }
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3 {
        color: black !important;
    }
    
    /* Header'ı gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    .stApp > header {display: none;}
    .stApp > div[data-testid="stToolbar"] {display: none;}
    .stApp > div[data-testid="stDecoration"] {display: none;}
    
    /* Özel buton CSS - Global */
    .st-emotion-cache-11byp7q {
        background-color: #FF6600 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: bold !important;
    }
    .st-emotion-cache-11byp7q:hover {
        background-color: #E55A00 !important;
        color: white !important;
    }
    
    /* Sidebar özel stilleri */
    [data-testid="stSidebar"] {
        background-color: black !important;
        width: 600px !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: white !important;
        border: none !important;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: normal;
        transition: background-color 0.3s;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    

    
    /* Login sayfası özel stilleri */
    .login-page .main {
        padding-top: 80px;
        padding-bottom: 40px;
        background-color: white;
        color: black;
    }
    .login-page h2, .login-page h3, .login-page p, .login-page label {
        color: black !important;
    }
    .login-page .stButton > button {
        background-color: #FF6600 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .login-page .stButton > button > div > p {
        color: white !important;
    }
    .login-page .stButton > button > div {
        color: white !important;
    }
    .login-page .stButton > button * {
        color: white !important;
    }
    .login-page .stButton > button:hover {
        background-color: #E55A00;
    }
    .login-page .stTextInput > div > div > input {
        border-radius: 6px !important;
        border: none !important;
        padding: 8px !important;
        font-size: 14px !important;
        background-color: white !important;
        color: black !important;
        box-shadow: none !important;
    }
    .login-page .stTextInput > div > div > input:focus {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .login-page .stTextInput > div > div > input::placeholder {
        color: black;
        opacity: 1;
    }
    .login-page .stTextInput > div > div > input:focus {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .login-page .stCheckbox > div > div > div {
        margin-top: 8px;
    }
    .login-page .stCheckbox > div > div > div > label {
        color: black !important;
    }
    .login-page a {
        color: black !important;
        text-decoration: none;
    }
    .login-page a:hover {
        color: #091C5A !important;
    }
    .login-page h2 {
        color: #091C5A !important;
    }
    

    

    

    
    /* Login ve OTP sayfası butonları için turuncu renk - EN SON */
    .login-page .stButton > button {
        background-color: #FF6600 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        transition: background-color 0.3s !important;
    }
    .login-page .stButton > button:hover {
        background-color: #E55A00 !important;
    }
    .login-page .stButton > button > div > p {
        color: white !important;
    }
    .login-page .stButton > button > div {
        color: white !important;
    }
    .login-page .stButton > button * {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# Dashboard sayfası
if st.session_state.logged_in:
    # Sidebar CSS
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #808080 !important;
        width: 300px !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: white !important;
        border: none !important;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: normal;
        transition: background-color 0.3s;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    /* Sidebar collapse butonunu gizle */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    button[kind="header"][data-testid="baseButton-header"] {
        display: none !important;
    }
    .css-1d391kg {
        display: none !important;
    }
    /* Ek collapse buton gizleme */
    [data-testid="stSidebar"] > div > div > div > button {
        display: none !important;
    }
    [data-testid="stSidebar"] button[aria-label="Close sidebar"] {
        display: none !important;
    }
    [data-testid="stSidebar"] .css-1cypcdb {
        display: none !important;
    }
    [data-testid="stSidebar"] .css-1d391kg {
        display: none !important;
    }
    .stSidebar > div > div > div > button {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sol sidebar
    with st.sidebar:
        # Logo tam ortalı
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        with col2:
            st.image("ing-logo.svg", width=280)
        st.markdown("")
        st.markdown("---")
        
        # Hoş geldin mesajı
        if st.session_state.username:
            user_info = USERS.get(st.session_state.username, {})
            approver_name = USERS.get(user_info.get('approver', ''), {}).get('name', user_info.get('approver', 'Bilinmiyor'))
            st.markdown(f"**Hoş geldin, {user_info.get('name', st.session_state.username)}!**")
            st.markdown(f"*Onaylayıcın: {approver_name}*")
            st.markdown("---")
        
        if st.button("🏠 Anasayfa", use_container_width=True, key="anasayfa_btn"):
            st.session_state.current_page = 'anasayfa'
            st.rerun()
            
        if st.button("📁 Dosya Yükleme", use_container_width=True, key="dosya_btn"):
            st.session_state.current_page = 'dosya_yukleme'
            st.rerun()
            
        if st.button("✅ Onay Ekranı", use_container_width=True, key="onay_btn"):
            st.session_state.current_page = 'onay_ekrani'
            st.rerun()
            
        if st.button("📜 Geçmiş", use_container_width=True, key="gecmis_btn"):
            st.session_state.current_page = 'gecmis'
            st.rerun()
        
        st.markdown("")
        st.markdown("---")
        
        # Çıkış yap butonu
        if st.button("Çıkış Yap", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.show_sms = False
            st.session_state.username = None
            # Query parametrelerini temizle
            st.query_params.clear()
            st.rerun()
    
    # Ana içerik - Sayfa kontrolü
    if st.session_state.current_page == 'anasayfa':
        # Dashboard yazı rengi CSS ve üst boşluk azaltma
        st.markdown("""
        <style>
        .stTitle h1 {
            color: black !important;
        }
        /* Sadece ana içerik alanını yukarı çek - Sidebar'ı koru */
        .stApp > div[data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 0rem !important;
            margin-top: -8rem !important;
            position: relative !important;
            z-index: 999 !important;
        }
        /* Ana içerik alanı için özel */
        section[data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 0rem !important;
            margin-top: -7rem !important;
        }
        /* Sidebar'ı koru */
        [data-testid="stSidebar"] {
            margin-top: 0rem !important;
            padding-top: 1rem !important;
            position: static !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("🏠 Anasayfa")
        
        # Kullanıcı bilgileri
        if st.session_state.username:
            user_info = USERS.get(st.session_state.username, {})
            approver_info = USERS.get(user_info.get('approver', ''), {})
            
            st.markdown(f"### 👋 Hoş Geldin, {user_info.get('name', st.session_state.username)}!")
            st.markdown("ING Data Entry Platform'a başarıyla giriş yaptınız.")
            st.markdown("---")
            
            # İki kolon: yetkiler ve onay ilişkisi
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 Yetkileriniz:**")
                st.markdown("- 📁 Dosya yükleme ve işleme")
                st.markdown("- 📝 Metadata ekleme")
                st.markdown("- ⚡ Quality rules tanımlama")
                st.markdown("- 📤 Dosyaları onaya gönderme")
                st.markdown("- ✅ Başkalarının dosyalarını onaylama")
                
            with col2:
                st.markdown("**🔗 Onay İlişkileri:**")
                st.markdown(f"**Sizin Onaylayıcınız:** {approver_info.get('name', 'Bilinmiyor')}")
                
                # Bu kullanıcının onaylayıcısı olduğu kişileri bul
                approves_for = []
                for username, info in USERS.items():
                    if info.get('approver') == st.session_state.username:
                        approves_for.append(info.get('name', username))
                
                if approves_for:
                    st.markdown("**Sizin Onayladığınız Kişiler:**")
                    for person in approves_for:
                        st.markdown(f"- {person}")
                else:
                    st.markdown("*Kimsenin onaylayıcısı değilsiniz*")
        else:
            st.markdown("### Hoş Geldiniz!")
            st.markdown("ING Data Entry Platform'a başarıyla giriş yaptınız.")
        
    elif st.session_state.current_page == 'dosya_yukleme':
        # Sidebar CSS (anasayfa ile aynı) ve üst boşluk azaltma
        st.markdown("""
        <style>
        /* Sidebar CSS - Anasayfa ile aynı */
        [data-testid="stSidebar"] {
            background-color: #808080 !important;
            width: 300px !important;
        }
        [data-testid="stSidebar"] .stMarkdown {
            color: white !important;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: white !important;
        }
        [data-testid="stSidebar"] p {
            color: white !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: transparent !important;
            color: white !important;
            border: none !important;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: normal;
            transition: background-color 0.3s;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
        }
        /* Sidebar collapse butonunu gizle */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        button[kind="header"][data-testid="baseButton-header"] {
            display: none !important;
        }
        .css-1d391kg {
            display: none !important;
        }
        /* Ek collapse buton gizleme */
        [data-testid="stSidebar"] > div > div > div > button {
            display: none !important;
        }
        [data-testid="stSidebar"] button[aria-label="Close sidebar"] {
            display: none !important;
        }
        [data-testid="stSidebar"] .css-1cypcdb {
            display: none !important;
        }
        [data-testid="stSidebar"] .css-1d391kg {
            display: none !important;
        }
        .stSidebar > div > div > div > button {
            display: none !important;
        }
        /* Logo ortalama */
        [data-testid="stSidebar"] .stImage {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        
        /* Sadece ana içerik alanını yukarı çek */
        .stApp > div[data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 0rem !important;
            margin-top: -12rem !important;
            position: relative !important;
            z-index: 999 !important;
        }
        /* Ana içerik alanı için özel */
        section[data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 0rem !important;
            margin-top: -10rem !important;
        }
        /* Ana içerik container'ını daha yukarı */
        .main .block-container {
            margin-top: -10rem !important;
            padding-top: 0rem !important;
        }
        /* Sidebar'ı koru */
        [data-testid="stSidebar"] {
            margin-top: 0rem !important;
            padding-top: 1rem !important;
            position: static !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("📁 Dosya Yükleme")
        
        # Tab sistemi için session state
        if 'uploaded_file_data' not in st.session_state:
            st.session_state.uploaded_file_data = None
        if 'df_data' not in st.session_state:
            st.session_state.df_data = None
        
        # Tab oluştur - normal Streamlit tabs kullan
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔒 Güvenlik", "📁 Dosya Yükleme", "📝 Metadata", "⚡ Data Quality", "📤 Onaya Gönder"])
        
        # Tab 1: Güvenlik Kontrolü
        with tab1:
            st.markdown("### Güvenlik Kontrolü")
            st.markdown("Dosya yüklemeden önce aşağıdaki güvenlik sorularını cevaplayın:")
            
            # Güvenlik soruları - Hizalama CSS
            st.markdown("""
            <style>
            /* Soru ve cevap hizalama */
            .stRadio > div {
                flex-direction: row !important;
                align-items: center !important;
                gap: 10px !important;
            }
            .stRadio > div > label {
                margin-bottom: 0rem !important;
                margin-right: 15px !important;
            }
            /* Soru boşluklarını azalt */
            .stMarkdown {
                margin-bottom: 0.2rem !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([2.5, 1.5])
            
            with col1:
                st.markdown("**1. Kişisel veri içerir mi?**")
            with col2:
                soru1 = st.radio("Soru1", ["Evet", "Hayır"], key="soru1", label_visibility="collapsed", horizontal=True)
            
            col1, col2 = st.columns([2.5, 1.5])
            
            with col1:
                st.markdown("**2. KVKK aykırı veri bulunuyor mu?**")
            with col2:
                soru2 = st.radio("Soru2", ["Evet", "Hayır"], key="soru2", label_visibility="collapsed", horizontal=True)
            
            col1, col2 = st.columns([2.5, 1.5])
            
            with col1:
                st.markdown("**3. Hassas veri bulunuyor mu?**")
            with col2:
                soru3 = st.radio("Soru3", ["Evet", "Hayır"], key="soru3", label_visibility="collapsed", horizontal=True)
            
            st.markdown("---")
            
            # Güvenlik kontrolü
            if soru1 == "Hayır" and soru2 == "Hayır" and soru3 == "Hayır":
                st.success("✅ Güvenlik kontrolü başarılı! **📁 Dosya Yükleme** sekmesine geçebilirsiniz.")
                st.session_state.security_passed = True
            else:
                st.error("❌ Güvenlik sorularının biri dahi olumsuz ise dosya yüklemeye izin verilmeyecektir.")
                st.session_state.security_passed = False
        
        # Tab 2: Dosya Yükleme
        with tab2:
            if not hasattr(st.session_state, 'security_passed') or not st.session_state.security_passed:
                st.warning("⚠️ Önce güvenlik kontrolünü tamamlayın.")
            else:
                st.markdown("### Dosya Yükleme")
                uploaded_file = st.file_uploader("Dosya seçin", type=['csv', 'xlsx', 'txt', 'pdf'], key="main_file_uploader")
                
                if uploaded_file is not None:
                    # Dosya bilgilerini session state'e kaydet
                    st.session_state.uploaded_file_data = {
                        'name': uploaded_file.name,
                        'size': uploaded_file.size,
                        'type': uploaded_file.type,
                        'content': uploaded_file
                    }
                    
                    # Dosya boyutunu MB'a çevir
                    file_size_mb = uploaded_file.size / (1024 * 1024)
                    
                    st.success(f"✅ Dosya tarandı: {uploaded_file.name}")
                    st.markdown(f"**Dosya boyutu:** {file_size_mb:.2f} MB")
                    st.markdown(f"**Dosya tipi:** {uploaded_file.type}")
                    
                    # Dosya önizlemesi - otomatik olarak burada göster
                    st.markdown("---")
                    st.markdown("### 📋 Dosya Önizleme")
                    
                    # Dosya preview - Yükleme animasyonu ile
                    with st.spinner('🔄 Önizleme yükleniyor...'):
                        try:
                            import pandas as pd
                            import io
                            import time
                            
                            # Kısa bekleme (gerçekçi yükleme hissi için)
                            time.sleep(0.5)
                            
                            # Dosya pointer'ını sıfırla
                            uploaded_file.seek(0)
                            
                            # Dosya tipine göre okuma
                            if uploaded_file.name.endswith('.csv'):
                                # CSV için encoding ve separator kontrolü
                                try:
                                    # İlk birkaç satırı oku ve kontrol et
                                    sample = uploaded_file.read(1024).decode('utf-8')
                                    uploaded_file.seek(0)
                                    
                                    # Separator tespiti
                                    if ';' in sample:
                                        separator = ';'
                                    elif ',' in sample:
                                        separator = ','
                                    elif '\t' in sample:
                                        separator = '\t'
                                    else:
                                        separator = ','
                                    
                                    df = pd.read_csv(uploaded_file, nrows=5, sep=separator, encoding='utf-8')
                                    uploaded_file.seek(0)
                                    st.session_state.df_data = pd.read_csv(uploaded_file, sep=separator, encoding='utf-8')
                                except UnicodeDecodeError:
                                    # UTF-8 başarısız ise latin-1 dene
                                    uploaded_file.seek(0)
                                    df = pd.read_csv(uploaded_file, nrows=5, encoding='latin-1')
                                    uploaded_file.seek(0)
                                    st.session_state.df_data = pd.read_csv(uploaded_file, encoding='latin-1')
                                    
                            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                                df = pd.read_excel(uploaded_file, nrows=5)
                                uploaded_file.seek(0)
                                st.session_state.df_data = pd.read_excel(uploaded_file)
                                
                            elif uploaded_file.name.endswith('.txt'):
                                # Text dosyası için
                                content = uploaded_file.read().decode('utf-8')
                                lines = content.split('\n')[:5]
                                st.markdown("**İlk 5 satır:**")
                                for i, line in enumerate(lines, 1):
                                    if line.strip():
                                        st.text(f"{i}. {line}")
                                uploaded_file.seek(0)
                            else:
                                st.info("📄 Bu dosya tipi için önizleme desteklenmiyor.")
                            
                            # DataFrame için preview
                            if uploaded_file.name.endswith(('.csv', '.xlsx', '.xls')):
                                if len(df.columns) > 0:
                                    st.markdown("**İlk 5 satır:**")
                                    st.dataframe(df, use_container_width=True)
                                    st.markdown(f"**Toplam sütun sayısı:** {len(df.columns)}")
                                    
                                    st.success("📝 **Metadata** sekmesine geçebilirsiniz!")
                                else:
                                    st.warning("⚠️ Dosyada hiç kolon bulunamadı. Dosya formatını kontrol edin.")
                                
                        except pd.errors.EmptyDataError:
                            st.warning("⚠️ Dosya boş görünüyor. Lütfen veri içeren bir dosya yükleyin.")
                        except pd.errors.ParserError as e:
                            st.warning(f"⚠️ Dosya parse hatası: Dosya formatını kontrol edin. Hata: {str(e)}")
                        except Exception as e:
                            st.warning(f"⚠️ Dosya önizleme hatası: {str(e)}")
                            st.info("💡 İpucu: CSV dosyaları için virgül, noktalı virgül veya tab ile ayrılmış formatları destekliyoruz.")
        
        # Tab 3: Metadata
        with tab3:
            if st.session_state.df_data is None:
                st.warning("⚠️ Önce dosya yükleyiniz.")
            else:
                st.markdown("### 📝 Kolon Metadata Düzenleme")
                st.markdown("Her kolon için açıklayıcı metadata ekleyin:")
                
                df = st.session_state.df_data
                
                # Session state'te metadata sakla
                if 'column_metadata' not in st.session_state:
                    st.session_state.column_metadata = {}
                
                # Her kolon için metadata input alanı
                for i, column in enumerate(df.columns):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.markdown(f"**{column}**")
                        # İlk birkaç değer örneği göster
                        sample_values = df[column].dropna().head(3).tolist()
                        if sample_values:
                            st.caption(f"Örnek: {', '.join(str(v) for v in sample_values)}")
                    
                    with col2:
                        # Her kolon için benzersiz key
                        metadata_key = f"metadata_{column}_{i}"
                        metadata_value = st.text_area(
                            "Metadata Açıklaması",
                            value=st.session_state.column_metadata.get(column, ""),
                            placeholder=f"{column} kolonu hakkında açıklayıcı bilgi girin...",
                            key=metadata_key,
                            height=80,
                            label_visibility="collapsed"
                        )
                        # Session state'i güncelle
                        st.session_state.column_metadata[column] = metadata_value
                
                # Metadata özeti
                st.markdown("---")
                st.markdown("### 📊 Metadata Özeti")
                
                # Metadata özeti metrikleri için CSS
                st.markdown("""
                <style>
                .stMetric {
                    color: black !important;
                }
                .stMetric > div {
                    color: black !important;
                }
                .stMetric [data-testid="metric-container"] {
                    color: black !important;
                }
                .stMetric [data-testid="metric-container"] > div {
                    color: black !important;
                }
                .stMetric label {
                    color: black !important;
                }
                .stMetric div[data-testid="metric-container"] div {
                    color: black !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                filled_metadata = {k: v for k, v in st.session_state.column_metadata.items() if v.strip()}
                total_columns = len(df.columns)
                filled_columns = len(filled_metadata)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam Kolon", total_columns)
                with col2:
                    st.metric("Metadata Eklenen", filled_columns)
                with col3:
                    completion_rate = (filled_columns / total_columns) * 100 if total_columns > 0 else 0
                    st.metric("Tamamlanma", f"{completion_rate:.0f}%")
                
                # Metadata kaydetme butonu
                if st.button("📋 Metadata'yı Kaydet", key="metadata_save_btn", use_container_width=True):
                    st.success("✅ Metadata başarıyla kaydedildi!")
                    # Metadata'yı göster
                    with st.expander("🔍 Kaydedilen Metadata'yı Görüntüle"):
                        for col, meta in filled_metadata.items():
                            st.markdown(f"**{col}:** {meta}")
                    
                    # Data Quality'ye yönlendirme
                    st.success("⚡ **Data Quality** sekmesine geçebilirsiniz!")
        
        # Tab 4: Data Quality
        with tab4:
            if st.session_state.df_data is None:
                st.warning("⚠️ Önce dosya yükleyiniz.")
            else:
                st.markdown("### ⚡ Data Quality Kuralları")
                st.markdown("Her kolon için veri kalitesi kuralları belirleyin:")
                
                df = st.session_state.df_data
                
                # Session state'te quality rules sakla
                if 'quality_rules' not in st.session_state:
                    st.session_state.quality_rules = {}
                
                # Quality rule seçenekleri
                quality_options = [
                    "Kural Seçiniz",
                    "Boş Değer Kontrolü (Not Null)",
                    "Benzersiz Değer Kontrolü (Unique)",
                    "Sayısal Değer Kontrolü (Numeric)",
                    "E-mail Format Kontrolü",
                    "Telefon Format Kontrolü", 
                    "Tarih Format Kontrolü",
                    "Minimum Uzunluk Kontrolü",
                    "Maksimum Uzunluk Kontrolü",
                    "Regex Pattern Kontrolü",
                    "Değer Aralığı Kontrolü (Min-Max)",
                    "İzin Verilen Değerler Listesi"
                ]
                
                # Her kolon için quality rule seçimi
                for i, column in enumerate(df.columns):
                    st.markdown("---")
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown(f"**{column}**")
                        # Kolon tipi ve örnek değerler
                        col_type = str(df[column].dtype)
                        st.caption(f"Tip: {col_type}")
                        sample_values = df[column].dropna().head(3).tolist()
                        if sample_values:
                            st.caption(f"Örnek: {', '.join(str(v) for v in sample_values)}")
                    
                    with col2:
                        # Quality rule seçimi
                        rule_key = f"quality_rule_{column}_{i}"
                        selected_rule = st.selectbox(
                            "Quality Rule",
                            quality_options,
                            key=rule_key,
                            label_visibility="collapsed"
                        )
                        
                        # Seçilen kurala göre ek parametreler
                        rule_params = {}
                        
                        if selected_rule == "Minimum Uzunluk Kontrolü":
                            min_length = st.number_input(
                                "Minimum uzunluk",
                                min_value=0,
                                value=1,
                                key=f"min_len_{column}_{i}"
                            )
                            rule_params['min_length'] = min_length
                            
                        elif selected_rule == "Maksimum Uzunluk Kontrolü":
                            max_length = st.number_input(
                                "Maksimum uzunluk",
                                min_value=1,
                                value=100,
                                key=f"max_len_{column}_{i}"
                            )
                            rule_params['max_length'] = max_length
                            
                        elif selected_rule == "Değer Aralığı Kontrolü (Min-Max)":
                            col_min, col_max = st.columns(2)
                            with col_min:
                                min_val = st.number_input(
                                    "Min değer",
                                    key=f"min_val_{column}_{i}"
                                )
                            with col_max:
                                max_val = st.number_input(
                                    "Max değer", 
                                    key=f"max_val_{column}_{i}"
                                )
                            rule_params['min_value'] = min_val
                            rule_params['max_value'] = max_val
                            
                        elif selected_rule == "Regex Pattern Kontrolü":
                            pattern = st.text_input(
                                "Regex Pattern",
                                placeholder="^[A-Za-z0-9]+$",
                                key=f"regex_{column}_{i}"
                            )
                            rule_params['pattern'] = pattern
                            
                        elif selected_rule == "İzin Verilen Değerler Listesi":
                            allowed_values = st.text_area(
                                "İzin verilen değerler (virgülle ayırın)",
                                placeholder="değer1, değer2, değer3",
                                key=f"allowed_{column}_{i}"
                            )
                            rule_params['allowed_values'] = [v.strip() for v in allowed_values.split(',') if v.strip()]
                        
                        # Session state'i güncelle
                        if selected_rule != "Kural Seçiniz":
                            st.session_state.quality_rules[column] = {
                                'rule': selected_rule,
                                'params': rule_params
                            }
                        elif column in st.session_state.quality_rules:
                            del st.session_state.quality_rules[column]
                
                # Quality Rules özeti
                st.markdown("---")
                st.markdown("### 📊 Quality Rules Özeti")
                
                # Quality Rules özeti metrikleri için CSS
                st.markdown("""
                <style>
                .stMetric {
                    color: black !important;
                }
                .stMetric > div {
                    color: black !important;
                }
                .stMetric [data-testid="metric-container"] {
                    color: black !important;
                }
                .stMetric [data-testid="metric-container"] > div {
                    color: black !important;
                }
                .stMetric label {
                    color: black !important;
                }
                .stMetric div[data-testid="metric-container"] div {
                    color: black !important;
                }
                /* Özel buton CSS */
                .st-emotion-cache-11byp7q {
                    background-color: #FF6600 !important;
                    color: white !important;
                    border: none !important;
                }
                .st-emotion-cache-11byp7q:hover {
                    background-color: #E55A00 !important;
                    color: white !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                applied_rules = {k: v for k, v in st.session_state.quality_rules.items() if v['rule'] != "Kural Seçiniz"}
                total_columns = len(df.columns)
                rules_applied = len(applied_rules)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam Kolon", total_columns)
                with col2:
                    st.metric("Kural Atanan", rules_applied)
                with col3:
                    completion_rate = (rules_applied / total_columns) * 100 if total_columns > 0 else 0
                    st.metric("Tamamlanma", f"{completion_rate:.0f}%")
                
                # Quality rules kaydetme butonu
                if st.button("⚡ Quality Rules'ı Kaydet", key="quality_save_btn", use_container_width=True):
                    st.success("✅ Quality Rules başarıyla kaydedildi!")
                    # Rules'ları göster
                    with st.expander("🔍 Kaydedilen Quality Rules'ları Görüntüle"):
                        for col, rule_info in applied_rules.items():
                            st.markdown(f"**{col}:** {rule_info['rule']}")
                            if rule_info['params']:
                                for param, value in rule_info['params'].items():
                                    st.markdown(f"  - {param}: {value}")
                
                st.success("📤 **Onaya Gönder** sekmesine geçebilirsiniz!")
        
        # Tab 5: Onaya Gönder
        with tab5:
            st.markdown("### 📤 İşlem Özeti ve Onay")
            
            # Özet bilgileri
            st.markdown("---")
            st.markdown("#### 📋 İşlem Durumu")
            
            # Güvenlik kontrolü durumu
            security_status = "✅ Geçildi" if hasattr(st.session_state, 'security_passed') and st.session_state.security_passed else "❌ Geçilmedi"
            st.markdown(f"**🔒 Güvenlik Adımı:** {security_status}")
            
            # Dosya yükleme durumu
            file_status = "✅ Yüklendi ve Önizlendi" if st.session_state.uploaded_file_data is not None and st.session_state.df_data is not None else "❌ Yüklenmedi"
            st.markdown(f"**📁 Dosya Eklendi:** {file_status}")
            
            # Metadata durumu
            metadata_count = len(st.session_state.column_metadata) if hasattr(st.session_state, 'column_metadata') else 0
            metadata_status = f"✅ {metadata_count} kolon için eklendi" if metadata_count > 0 else "❌ Eklenmedi"
            st.markdown(f"**📝 Metadata:** {metadata_status}")
            
            # Quality Rules durumu
            quality_count = len([k for k, v in st.session_state.quality_rules.items() if v['rule'] != "Kural Seçiniz"]) if hasattr(st.session_state, 'quality_rules') else 0
            quality_status = f"✅ {quality_count} kolon için eklendi" if quality_count > 0 else "❌ Eklenmedi"
            st.markdown(f"**⚡ Quality Rules:** {quality_status}")
            
            st.markdown("---")
            
            # Dosya bilgileri (eğer yüklenmiş ise)
            if st.session_state.uploaded_file_data is not None:
                st.markdown("#### 📄 Dosya Bilgileri")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Dosya Adı", st.session_state.uploaded_file_data['name'])
                with col2:
                    file_size_mb = st.session_state.uploaded_file_data['size'] / (1024 * 1024)
                    st.metric("Dosya Boyutu", f"{file_size_mb:.2f} MB")
                with col3:
                    column_count = len(st.session_state.df_data.columns) if st.session_state.df_data is not None else 0
                    st.metric("Kolon Sayısı", column_count)
                
                st.markdown("---")
            
            # Onay butonu - sadece tüm adımlar tamamlandıysa aktif
            can_approve = (
                hasattr(st.session_state, 'security_passed') and st.session_state.security_passed and
                st.session_state.uploaded_file_data is not None and
                st.session_state.df_data is not None
            )
            
            if not can_approve:
                st.warning("⚠️ Dosyayı S3'e yüklemek için önce güvenlik kontrolü ve dosya yükleme adımlarını tamamlayın.")
            else:
                st.info("🎯 Tüm adımlar tamamlandı. Dosyayı onaya gönderebilirsiniz.")
                
                # Comment alanı
                st.markdown("### 💬 Onaylayıcıya Not")
                comment = st.text_area(
                    "Onaylayıcıya iletmek istediğiniz notu buraya yazabilirsiniz:",
                    placeholder="Örnek: Bu dosya müşteri verilerini içeriyor, dikkatli inceleme yapılması gerekiyor...",
                    height=100,
                    key="approval_comment"
                )
                
                # Onaya gönderme butonu
                if st.button("📤 Onaya Gönder", type="primary", use_container_width=True):
                    try:
                        import json
                        import zipfile
                        import io
                        from datetime import datetime
                        
                        with st.spinner("📋 Dosya onaya hazırlanıyor..."):
                            # Dosya adı ve metadata hazırla
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            original_filename = st.session_state.uploaded_file_data['name']
                            
                            # Ana dosya içeriğini hazırla
                            file_content = st.session_state.uploaded_file_data['content']
                            file_content.seek(0)
                            file_data = file_content.read()
                            original_file_size = len(file_data)
                            
                            # Metadata JSON'u oluştur
                            metadata_json = {
                                "upload_timestamp": timestamp,
                                "uploader": st.session_state.username,
                                "approver": USERS.get(st.session_state.username, {}).get('approver'),
                                "original_filename": original_filename,
                                "file_size_mb": round(original_file_size / (1024 * 1024), 2),
                                "file_type": st.session_state.uploaded_file_data['type'],
                                "columns": list(st.session_state.df_data.columns.tolist()) if st.session_state.df_data is not None else [],
                                "metadata": st.session_state.column_metadata if hasattr(st.session_state, 'column_metadata') else {},
                                "quality_rules": st.session_state.quality_rules if hasattr(st.session_state, 'quality_rules') else {},
                                "security_check_passed": True,
                                "status": "pending_approval",
                                "comment": comment if comment else "Not eklenmedi"
                            }
                            
                            # ZIP dosyası oluştur (memory'de tut)
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                # Ana dosyayı ZIP'e ekle
                                zip_file.writestr(original_filename, file_data)
                                # Metadata'yı ZIP'e ekle
                                zip_file.writestr(f"{original_filename}_metadata.json", json.dumps(metadata_json, indent=2, ensure_ascii=False).encode('utf-8'))
                            
                            zip_buffer.seek(0)
                            zip_data = zip_buffer.read()
                            
                            # Pending uploads listesine ekle
                            upload_item = {
                                "id": f"{timestamp}_{st.session_state.username}_{original_filename}",
                                "timestamp": timestamp,
                                "uploader": st.session_state.username,
                                "approver": USERS.get(st.session_state.username, {}).get('approver'),
                                "filename": original_filename,
                                "file_size_mb": round(original_file_size / (1024 * 1024), 2),
                                "zip_data": zip_data,
                                "metadata": metadata_json,
                                "status": "pending_approval",
                                "comment": comment if comment else "Not eklenmedi"
                            }
                            
                            st.session_state.pending_uploads.append(upload_item)
                            
                            # History'ye kayıt ekle
                            history_item = {
                                "timestamp": timestamp,
                                "action": "upload_submitted",
                                "user": st.session_state.username,
                                "filename": original_filename,
                                "file_size_mb": round(original_file_size / (1024 * 1024), 2),
                                "approver": USERS.get(st.session_state.username, {}).get('approver'),
                                "status": "pending_approval",
                                "comment": comment if comment else "Not eklenmedi",
                                "details": f"Dosya onaya gönderildi - {approver_name} tarafından onaylanacak"
                            }
                            st.session_state.history.append(history_item)
                            
                            st.balloons()
                            st.success("🎉 Dosya başarıyla onaya gönderildi!")
                            
                            # Onay detayları
                            approver_name = USERS.get(metadata_json['approver'], {}).get('name', metadata_json['approver'])
                            with st.expander("📋 Onay Detayları"):
                                st.markdown(f"**👤 Yükleyen:** {USERS.get(st.session_state.username, {}).get('name', st.session_state.username)}")
                                st.markdown(f"**👑 Onaylayıcı:** {approver_name}")
                                st.markdown(f"**📁 Dosya:** `{original_filename}`")
                                st.markdown(f"**📏 Boyut:** {round(original_file_size / (1024 * 1024), 2)} MB")
                                st.markdown(f"**🕒 Gönderim Zamanı:** {timestamp}")
                                st.markdown(f"**📊 Durum:** ⏳ Onay Bekliyor")
                                
                            st.info(f"💡 Dosyanız {approver_name} tarafından onaylandıktan sonra S3'e yüklenecektir.")
                            
                    except Exception as e:
                        st.error(f"❌ Onaya gönderme hatası: {str(e)}")
    
    elif st.session_state.current_page == 'onay_ekrani':
        # Onay Ekranı sayfası CSS ve üst boşluk azaltma
        st.markdown("""
        <style>
        .stTitle h1 {
            color: black !important;
        }
        /* Sadece ana içerik alanını yukarı çek - Sidebar'ı koru */
        .stApp > div[data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 0rem !important;
            margin-top: -12rem !important;
            position: relative !important;
            z-index: 999 !important;
        }
        /* Ana içerik alanı için özel */
        section[data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 0rem !important;
            margin-top: -10rem !important;
        }
        /* Ana içerik container'ını daha yukarı */
        .main .block-container {
            margin-top: -10rem !important;
            padding-top: 0rem !important;
        }
        /* Sidebar'ı koru */
        [data-testid="stSidebar"] {
            margin-top: 0rem !important;
            padding-top: 1rem !important;
            position: static !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("✅ Onay Ekranı")
        
        # Kullanıcının onaylaması gereken kişileri kontrol et
        if st.session_state.username:
            approves_for = []
            for username, info in USERS.items():
                if info.get('approver') == st.session_state.username:
                    approves_for.append(info.get('name', username))
            
            if not approves_for:
                st.warning("⚠️ Kimsenin onaylayıcısı olmadığınız için onaylayacak dosya bulunmuyor.")
                st.stop()
        
        # Pending uploads listesinden dosyaları listele
        st.markdown("### 📋 Onay Bekleyen Dosyalar")
        
        # Bu kullanıcının onaylaması gereken dosyaları filtrele
        pending_for_user = []
        for upload in st.session_state.pending_uploads:
            if upload.get('approver') == st.session_state.username and upload.get('status') == 'pending_approval':
                pending_for_user.append(upload)
        
        if not pending_for_user:
            st.info("📝 Henüz onay bekleyen dosya bulunmuyor.")
        else:
            st.success(f"📊 {len(pending_for_user)} dosya onay bekliyor.")
            
            # Her dosya için onay kartı
            for upload in pending_for_user:
                uploader_name = USERS.get(upload['uploader'], {}).get('name', upload['uploader'])
                with st.expander(f"📦 {upload['filename']} - {uploader_name}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        metadata = upload['metadata']
                        st.markdown(f"**👤 Yükleyen:** {uploader_name}")
                        st.markdown(f"**📁 Dosya:** `{upload['filename']}`")
                        st.markdown(f"**📏 Boyut:** {upload['file_size_mb']} MB")
                        st.markdown(f"**🕒 Yükleme Tarihi:** {upload['timestamp']}")
                        
                        st.markdown("**📋 Dosya Bilgileri:**")
                        st.markdown(f"- **Dosya Tipi:** {metadata.get('file_type', 'N/A')}")
                        st.markdown(f"- **Kolon Sayısı:** {len(metadata.get('columns', []))}")
                        st.markdown(f"- **Güvenlik Kontrolü:** {'✅ Geçti' if metadata.get('security_check_passed') else '❌ Geçmedi'}")
                        
                        if metadata.get('metadata'):
                            st.markdown(f"- **Metadata:** {len(metadata.get('metadata', {}))} kolon için eklendi")
                        if metadata.get('quality_rules'):
                            quality_count = len([k for k, v in metadata.get('quality_rules', {}).items() if v.get('rule') != 'Kural Seçiniz'])
                            st.markdown(f"- **Quality Rules:** {quality_count} kolon için eklendi")
                        
                        # Comment göster
                        if upload.get('comment') and upload['comment'] != "Not eklenmedi":
                            st.markdown("**💬 Yükleyen Notu:**")
                            st.info(f"_{upload['comment']}_")
                    
                    with col2:
                        st.markdown("**🎯 İşlemler:**")
                        
                        # Yükle butonu (S3'e yükle)
                        if st.button("📤 Yükle", key=f"upload_{upload['id']}", use_container_width=True):
                            try:
                                import boto3
                                import io
                                from datetime import datetime
                                from botocore.exceptions import ClientError, NoCredentialsError
                                
                                # S3 bağlantı bilgileri (environment variables'dan al)
                                import os
                                s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
                                aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
                                aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin123")
                                bucket_name = os.getenv("S3_BUCKET_NAME", "data-uploads")
                                region_name = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                                
                                with st.spinner("📦 Dosya S3'e yükleniyor..."):
                                    # S3 client oluştur
                                    s3_client = boto3.client(
                                        's3',
                                        endpoint_url=s3_endpoint_url,
                                        aws_access_key_id=aws_access_key_id,
                                        aws_secret_access_key=aws_secret_access_key,
                                        region_name=region_name
                                    )
                                    
                                    # Bucket var mı kontrol et, yoksa oluştur
                                    try:
                                        s3_client.head_bucket(Bucket=bucket_name)
                                    except ClientError as e:
                                        error_code = e.response['Error']['Code']
                                        if error_code == '404':
                                            # Bucket yok, oluştur
                                            s3_client.create_bucket(Bucket=bucket_name)
                                        else:
                                            raise e
                                    
                                    # ZIP dosyasını S3'e yükle
                                    zip_filename = f"approved/{upload['timestamp']}_{upload['filename']}.zip"
                                    s3_client.put_object(
                                        Bucket=bucket_name,
                                        Key=zip_filename,
                                        Body=io.BytesIO(upload['zip_data']),
                                        ContentType="application/zip"
                                    )
                                    
                                    # Upload'ın durumunu güncelle
                                    upload['status'] = 'approved'
                                    
                                    # History'ye onaylama kaydı ekle
                                    from datetime import datetime
                                    approval_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    history_item = {
                                        "timestamp": approval_timestamp,
                                        "action": "file_approved",
                                        "user": st.session_state.username,
                                        "filename": upload['filename'],
                                        "file_size_mb": upload['file_size_mb'],
                                        "uploader": upload['uploader'],
                                        "status": "approved",
                                        "details": f"Dosya onaylandı ve S3'e yüklendi - {zip_filename}"
                                    }
                                    st.session_state.history.append(history_item)
                                    
                                    st.balloons()
                                    st.success("🎉 Dosya başarıyla S3'e yüklendi!")
                                    st.info(f"📁 Dosya konumu: `{zip_filename}`")
                                    st.rerun()
                                    
                            except NoCredentialsError:
                                st.error("❌ AWS kimlik bilgileri bulunamadı!")
                            except ClientError as e:
                                st.error(f"❌ S3 hatası: {e.response['Error']['Message']}")
                            except Exception as e:
                                st.error(f"❌ Yükleme hatası: {str(e)}")
                        
                        # Red butonu
                        if st.button("❌ Reddet", key=f"reject_{upload['id']}", use_container_width=True):
                            upload['status'] = 'rejected'
                            
                            # History'ye reddetme kaydı ekle
                            from datetime import datetime
                            reject_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            history_item = {
                                "timestamp": reject_timestamp,
                                "action": "file_rejected",
                                "user": st.session_state.username,
                                "filename": upload['filename'],
                                "file_size_mb": upload['file_size_mb'],
                                "uploader": upload['uploader'],
                                "status": "rejected",
                                "details": f"Dosya reddedildi"
                            }
                            st.session_state.history.append(history_item)
                            
                            st.warning("❌ Dosya reddedildi!")
                            st.rerun()
                        
                        # İndir butonu
                        if st.button("📥 İndir", key=f"download_{upload['id']}", use_container_width=True):
                            st.download_button(
                                label="💾 ZIP Dosyasını İndir",
                                data=upload['zip_data'],
                                file_name=f"{upload['filename']}.zip",
                                mime="application/zip",
                                key=f"download_btn_{upload['id']}",
                                use_container_width=True
                            )

    elif st.session_state.current_page == 'gecmis':
        # Geçmiş sayfası CSS ve üst boşluk azaltma
        st.markdown("""
        <style>
        .stTitle h1 {
            color: black !important;
        }
        /* Sadece ana içerik alanını yukarı çek - Sidebar'ı koru */
        .stApp > div[data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 0rem !important;
            margin-top: -12rem !important;
            position: relative !important;
            z-index: 999 !important;
        }
        /* Ana içerik alanı için özel */
        section[data-testid="stAppViewContainer"] .main .block-container {
            padding-top: 0rem !important;
            margin-top: -10rem !important;
        }
        /* Ana içerik container'ını daha yukarı */
        .main .block-container {
            margin-top: -10rem !important;
            padding-top: 0rem !important;
        }
        /* Sidebar'ı koru */
        [data-testid="stSidebar"] {
            margin-top: 0rem !important;
            padding-top: 1rem !important;
            position: static !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("📜 Geçmiş")
        
        # Kullanıcının geçmişini filtrele
        user_history = []
        for item in st.session_state.history:
            # Kullanıcının kendi işlemleri veya onayladığı/reddettiği işlemler
            if (item.get('user') == st.session_state.username or 
                item.get('uploader') == st.session_state.username):
                user_history.append(item)
        
        if not user_history:
            st.info("📝 Henüz geçmiş kaydı bulunmuyor.")
        else:
            st.success(f"📊 {len(user_history)} geçmiş kaydı bulundu.")
            
            # Geçmiş kayıtlarını tarihe göre sırala (en yeni üstte)
            user_history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Her kayıt için kart
            for item in user_history:
                # İşlem türüne göre renk ve ikon belirle
                if item['action'] == 'upload_submitted':
                    color = "blue"
                    icon = "📤"
                    title = "Dosya Onaya Gönderildi"
                elif item['action'] == 'file_approved':
                    color = "green"
                    icon = "✅"
                    title = "Dosya Onaylandı"
                elif item['action'] == 'file_rejected':
                    color = "red"
                    icon = "❌"
                    title = "Dosya Reddedildi"
                else:
                    color = "gray"
                    icon = "📋"
                    title = "Diğer İşlem"
                
                with st.expander(f"{icon} {title} - {item['filename']}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**📁 Dosya:** `{item['filename']}`")
                        st.markdown(f"**📏 Boyut:** {item['file_size_mb']} MB")
                        st.markdown(f"**🕒 Tarih:** {item['timestamp']}")
                        st.markdown(f"**👤 İşlemi Yapan:** {USERS.get(item['user'], {}).get('name', item['user'])}")
                        
                        if item['action'] == 'upload_submitted':
                            approver_name = USERS.get(item['approver'], {}).get('name', item['approver'])
                            st.markdown(f"**👑 Onaylayıcı:** {approver_name}")
                        elif item['action'] in ['file_approved', 'file_rejected']:
                            uploader_name = USERS.get(item['uploader'], {}).get('name', item['uploader'])
                            st.markdown(f"**👤 Yükleyen:** {uploader_name}")
                        
                        st.markdown(f"**📋 Detay:** {item['details']}")
                        
                        # Comment göster (sadece upload_submitted için)
                        if item['action'] == 'upload_submitted' and item.get('comment') and item['comment'] != "Not eklenmedi":
                            st.markdown("**💬 Yükleyen Notu:**")
                            st.info(f"_{item['comment']}_")
                    
                    with col2:
                        # Durum badge'i
                        if item['status'] == 'pending_approval':
                            st.markdown("**📊 Durum:** ⏳ Onay Bekliyor")
                        elif item['status'] == 'approved':
                            st.markdown("**📊 Durum:** ✅ Onaylandı")
                        elif item['status'] == 'rejected':
                            st.markdown("**📊 Durum:** ❌ Reddedildi")
                        
                        # İşlem türü
                        st.markdown(f"**🎯 İşlem:** {title}")

# SMS doğrulama sayfası
elif st.session_state.show_sms:
    st.markdown("""
    <style>
    .login-page .stButton > button {
        background-color: #FF6600 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: bold !important;
    }
    .login-page .stButton > button:hover {
        background-color: #E55A00 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-page">', unsafe_allow_html=True)
    with st.container():
        # Logo - ortalanmış ve büyütülmüş
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
            </div>
            """, unsafe_allow_html=True)
            # Logo resmi - 4 kat büyütülmüş (200 * 4 = 800px)
            st.image("ing-logo.svg", width=800)
        
        # Logo ile form arası boşluk
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.markdown("")
        
        # SMS doğrulama kodu - login formu ile aynı boyut
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <style>
            .stTextInput > div > div > input {
                border: none !important;
                background-color: white !important;
                color: black !important;
                box-shadow: none !important;
                outline: none !important;
            }
            .stTextInput > div > div > input:focus {
                border: none !important;
                box-shadow: none !important;
                outline: none !important;
            }
            .stTextInput > div > div > input::placeholder {
                color: black !important;
                opacity: 1 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            # INGKey notu
            st.markdown("""
            <div style="text-align: center; margin-bottom: 20px; color: #666; font-size: 14px;">
                <a href="https://ing.com.tr/auth" target="_blank" style="color: #FF6600; text-decoration: none; font-weight: bold;">INGKey</a> uygulamasından alınacak şifreyi giriniz.
            </div>
            """, unsafe_allow_html=True)
            
            sms_code = st.text_input("SMS Kodu", placeholder="INGKEY ŞİFRESİ GİRİNİZ", type="password", label_visibility="collapsed")
            
            # Onayla butonu
            st.markdown("""
            <style>
            .stButton > button {
                background-color: #FF6600 !important;
                color: white !important;
                border: none !important;
                padding: 12px 24px !important;
                border-radius: 8px !important;
                font-size: 16px !important;
                font-weight: bold !important;
            }
            .stButton > button:hover {
                background-color: #E55A00 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            verify_button = st.button("Onayla", use_container_width=True)
            
            # Geri dön butonu
            if st.button("Geri Dön"):
                st.session_state.show_sms = False
                st.rerun()
        
        if verify_button:
            if sms_code == "654123":
                st.success("✅ Giriş başarılı!")
                # Dashboard'a yönlendir
                st.session_state.logged_in = True
                st.session_state.show_sms = False
                st.rerun()
            else:
                st.error("❌ SMS kodu hatalı")
    st.markdown('</div>', unsafe_allow_html=True)

# Giriş kutusu
else:
    st.markdown("""
    <style>
    .login-page .stButton > button {
        background-color: #FF6600 !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: bold !important;
    }
    .login-page .stButton > button:hover {
        background-color: #E55A00 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-page">', unsafe_allow_html=True)
    with st.container():
        # Logo - ortalanmış ve büyütülmüş
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
            </div>
            """, unsafe_allow_html=True)
            # Logo resmi - 4 kat büyütülmüş (200 * 4 = 800px)
            st.image("ing-logo.svg", width=800)
            

        
        # Logo ile form arası boşluk
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.markdown("")
        
        # Form container - daha dar
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <style>
            .stTextInput > div > div > input {
                border: none !important;
                background-color: white !important;
                color: black !important;
                box-shadow: none !important;
                outline: none !important;
            }
            .stTextInput > div > div > input:focus {
                border: none !important;
                box-shadow: none !important;
                outline: none !important;
            }
            .stTextInput > div > div > input::placeholder {
                color: black !important;
                opacity: 1 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            username = st.text_input("Kullanıcı Adı", placeholder="1.Kullanıcı", label_visibility="collapsed")
            password = st.text_input("Şifre", type="password", placeholder="••••••••", label_visibility="collapsed")

            col1, col2 = st.columns([1, 2])
            with col1:
                remember_me = st.checkbox("Beni hatırla")
            with col2:
                st.markdown("<p style='text-align: right'><a href='#'>Şifremi unuttum?</a></p>", unsafe_allow_html=True)

            st.markdown("""
            <style>
            .stButton > button {
                background-color: #FF6600 !important;
                color: white !important;
                border: none !important;
                padding: 12px 24px !important;
                border-radius: 8px !important;
                font-size: 16px !important;
                font-weight: bold !important;
            }
            .stButton > button:hover {
                background-color: #E55A00 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            login_button = st.button("Giriş Yap", use_container_width=True)

        if login_button:
            if username and password:
                # LDAP ile kullanıcı doğrulama
                auth_success, auth_message = ldap_authenticate(username, password)
                
                if auth_success:
                    # Kullanıcı bilgilerini session'a kaydet
                    st.session_state.username = username
                    # SMS doğrulama sayfasına yönlendir
                    st.session_state.show_sms = True
                    st.rerun()
                else:
                    st.error(f"❌ {auth_message}")
            else:
                st.error("❌ Kullanıcı adı ve şifre gerekli")
    st.markdown('</div>', unsafe_allow_html=True) 