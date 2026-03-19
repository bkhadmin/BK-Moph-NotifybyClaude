from pathlib import Path
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name:str='BK-Moph Notify'
    app_env:str='production'
    app_debug:bool=False
    app_secret_key:str='change-me'
    app_url:str='http://127.0.0.1:8012'
    allowed_origins:str='http://127.0.0.1:8012'
    trusted_hosts:str='127.0.0.1,localhost,app,app:8000,nginx,bk_app'
    session_cookie_name:str='bk_notify_session'
    session_expire_hours:int=12
    session_cookie_secure:bool=False
    session_cookie_samesite:str='lax'
    csrf_enabled:bool=True
    csrf_cookie_name:str='bk_notify_csrf'
    csrf_header_name:str='x-csrf-token'
    mysql_host:str='mysql'
    mysql_port:int=3306
    mysql_database:str='bk_moph_notify'
    mysql_user:str='bknotify'
    mysql_password:str='change-me'
    redis_url:str='redis://redis:6379/0'
    internal_superadmin_username:str='superadmin'
    internal_superadmin_password:str='BkhAdmin@11252'
    login_fail_limit:int=5
    ip_ban_threshold:int=15
    ip_ban_window_minutes:int=30

    upload_dir:str='/app/storage/uploads'
    image_public_base:str='/static/uploads'
    max_upload_mb:int=5

    provider_login_enabled:bool=True
    health_id_base_url:str='https://moph.id.th'
    health_id_client_id:str=''
    health_id_client_secret:str=''
    health_id_redirect_uri:str=''
    health_id_scope:str='openid profile'
    provider_base_url:str='https://provider.id.th'
    provider_client_id:str=''
    provider_secret_key:str=''
    provider_profile_url:str='https://provider.id.th/api/v1/services/profile'
    provider_service_token_url:str='https://provider.id.th/api/v1/services/token'
    provider_profile_moph_center_token:int=0
    provider_profile_moph_idp_permission:int=1
    provider_profile_position_type:int=1

    moph_notify_base_url:str='https://morpromt2f.moph.go.th'
    moph_notify_send_path:str='/api/notify/send'
    moph_notify_client_key:str=''
    moph_notify_secret_key:str=''

    hosxp_db_host:str=''
    hosxp_db_port:int=3306
    hosxp_db_name:str='hosxp'
    hosxp_db_user:str=''
    hosxp_db_password:str=''
    hosxp_db_charset:str='utf8mb4'
    max_query_rows:int=200
    max_query_seconds:int=20

    model_config=SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False)

    @property
    def allowed_origins_list(self):
        return [x.strip() for x in self.allowed_origins.split(',') if x.strip()]

    @property
    def sqlalchemy_database_uri(self)->str:
        return f"mysql+pymysql://{self.mysql_user}:{quote_plus(self.mysql_password)}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"

    @property
    def hosxp_database_uri(self)->str:
        return f"mysql+pymysql://{self.hosxp_db_user}:{quote_plus(self.hosxp_db_password)}@{self.hosxp_db_host}:{self.hosxp_db_port}/{self.hosxp_db_name}?charset={self.hosxp_db_charset}"

    @property
    def upload_path(self)->Path:
        return Path(self.upload_dir)

settings=Settings()
