from app.repositories.role_permissions import get_permission_codes_for_role
MENU_PERMISSIONS={'dashboard':'menu.dashboard','users':'menu.users','logs':'menu.logs','rbac':'menu.rbac','notify':'menu.notify','queries':'menu.queries','templates':'menu.templates','schedules':'menu.schedules','media':'menu.media'}
def allowed_menu(db, role_id:int|None, menu_code:str)->bool:
    if not role_id: return False
    required=MENU_PERMISSIONS.get(menu_code)
    return required in get_permission_codes_for_role(db, role_id) if required else False
