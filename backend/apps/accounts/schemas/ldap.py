from ninja import Field, Schema


class LdapSettingsBase(Schema):
    enabled: bool
    server_uri: str
    start_tls: bool
    verify_cert: bool
    ca_cert_file: str
    timeout: int = Field(ge=1, le=120)
    bind_dn: str
    user_search_base: str
    user_filter: str
    attr_username: str
    attr_first_name: str
    attr_last_name: str
    attr_employee_number: str
    attr_email: str
    attr_job_title: str
    attr_phone: str
    create_users: bool


class LdapSettingsOut(LdapSettingsBase):
    """Effective configuration; the bind password itself is never returned."""

    bind_password_set: bool
    locked: list[str] = Field(description="Fields set by LDAP_* environment variables (read-only).")
    env_names: dict[str, str]


class LdapSettingsIn(LdapSettingsBase):
    # None keeps the stored password, "" clears it.
    bind_password: str | None = None


class LdapTestIn(LdapSettingsIn):
    username: str = ""


class LdapTestOut(Schema):
    server: str
    user: dict[str, str] | None
