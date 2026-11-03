export default {
  appearance: {
    title: 'Darstellung',
    subtitle:
      'Wie Argus für Sie aussieht. Wird in Ihrem Profil gespeichert und gilt auf jedem Gerät.',
    theme: 'Farbschema',
    themeDescription: 'System folgt der hellen oder dunklen Einstellung Ihres Geräts.',
    groups: { system: 'System', light: 'Helle Themes', dark: 'Dunkle Themes' },
  },
  notifications: {
    title: 'Benachrichtigungen',
    subtitle:
      'Legen Sie fest, welche Benachrichtigungen Sie in der App und per E-Mail an {email} erhalten.',
    employeeDescription: 'Zu Ihren Anforderungen, Geräten und Meldungen.',
    itDescription: 'Für IT-Mitarbeiter.',
    approverDescription: 'Für Genehmiger von Abteilungen.',
    mailOff: 'Der E-Mail-Versand ist derzeit deaktiviert.',
    noEmail: 'Für Ihr Konto ist keine E-Mail-Adresse hinterlegt. Bitte wenden Sie sich an die IT.',
    noneActive: 'Die IT hat derzeit keine Benachrichtigungen für Sie eingeschaltet.',
  },
  security: {
    title: 'Anmeldung & Sicherheit',
    subtitle: 'Zwei-Faktor-Authentifizierung und Backup-Codes für Ihr Konto.',
    twoFactor: 'Zwei-Faktor-Authentifizierung (2FA)',
    twoFactorDescription:
      'Zusätzlich zum Passwort ist bei der Anmeldung ein Einmalcode erforderlich – aus einer Authenticator-App oder per E-Mail.',
    on: 'Aktiv · {method}',
    off: 'Inaktiv',
    inUse: 'In Verwendung',
    setUp: 'Einrichten',
    switchTo: 'Wechseln',
    emailUnavailable:
      'Nicht verfügbar: keine E-Mail-Adresse hinterlegt oder E-Mail-Versand deaktiviert',
    methods: {
      totp: 'Authenticator-App',
      totpHelp: 'Empfohlen. Z. B. Microsoft Authenticator oder 1Password.',
      email: 'Code per E-Mail',
      emailHelp: 'Bei jeder Anmeldung wird ein Code an Ihre E-Mail-Adresse gesendet.',
    },
    backupCodes: 'Backup-Codes',
    backupDescription:
      'Ermöglichen die Anmeldung, wenn Authenticator-App oder Postfach nicht verfügbar sind. Jeder Code ist nur einmal gültig.',
    codesLeft:
      'Keine Backup-Codes verfügbar | 1 Backup-Code verfügbar | {count} Backup-Codes verfügbar',
    fewCodes: 'Nur noch {count} Backup-Codes verfügbar. Erzeugen Sie rechtzeitig neue Codes.',
    renew: 'Neue Codes erzeugen',
    renewText:
      'Es werden zehn neue Backup-Codes erzeugt; die bisherigen werden ungültig. Bestätigen Sie mit Ihrem Passwort.',
    codesText: 'Codes sicher aufbewahren. Sie werden nur einmal angezeigt.',
    codesStored: 'Ich habe die Codes sicher gespeichert.',
    codesFileTitle: 'Argus – Backup-Codes für {user}',
    codesFileHint: 'Jeder Code ist für genau eine Anmeldung gültig.',
    copy: 'Kopieren',
    copied: 'In die Zwischenablage kopiert',
    download: 'Als Textdatei speichern',
    finish: 'Fertig',
    disable: 'Zwei-Faktor-Authentifizierung deaktivieren',
    disableHelp:
      'Die Anmeldung erfolgt danach nur mit Passwort. Vorhandene Backup-Codes werden gelöscht.',
    disableText: 'Bestätigen Sie mit Ihrem Passwort.',
    disabled: 'Zwei-Faktor-Authentifizierung deaktiviert',
    setup: {
      totpTitle: 'Authenticator-App einrichten',
      emailTitle: 'Code per E-Mail einrichten',
      stepPassword: 'Passwort',
      stepVerify: 'Einrichten',
      stepCodes: 'Backup-Codes',
      passwordText: 'Bestätigen Sie zunächst Ihr Passwort.',
      next: 'Weiter',
      scanText:
        'Scannen Sie den QR-Code mit Ihrer Authenticator-App und geben Sie den angezeigten Code ein.',
      qrAlt: 'QR-Code für die Authenticator-App',
      manualText: 'Alternativ den Schlüssel manuell in der App eingeben:',
      emailText:
        'Ein 6-stelliger Code wurde an {email} gesendet. Geben Sie ihn zur Bestätigung ein.',
      emailFailed:
        'Der Code konnte nicht gesendet werden. Fordern Sie ihn erneut an oder wenden Sie sich an die IT.',
      activate: 'Aktivieren',
      activated: 'Die Zwei-Faktor-Authentifizierung ist aktiv.',
    },
  },
}
