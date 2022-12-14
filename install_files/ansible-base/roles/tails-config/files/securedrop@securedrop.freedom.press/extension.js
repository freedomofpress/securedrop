/* exported init */

const GETTEXT_DOMAIN = 'securedrop';

const {Clutter, GObject, GLib, St } = imports.gi;

const Util = imports.misc.util;
const ExtensionUtils = imports.misc.extensionUtils;
const Main = imports.ui.main;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;

const _ = ExtensionUtils.gettext;

const Indicator = GObject.registerClass(
class Indicator extends PanelMenu.Button {
    _init() {
        super._init(0.0, _('SecureDrop'));

        let icon = new St.Icon({
            icon_name: 'package-x-generic-symbolic',
            style_class: 'system-status-icon',
        });
        
        let label = new St.Label({
            text: _('SecureDrop'),
            y_expand: true,
            y_align: Clutter.ActorAlign.CENTER,
        });
        
        let topBox = new St.BoxLayout({
            style_class: 'panel-status-menu-box'
        });
        
        topBox.add_child(icon);
        topBox.add_child(label);
        this.add_child(topBox);

        let source = new PopupMenu.PopupMenuItem(_('Launch Source Interface'));
        source.connect('activate', () => {
            Util.trySpawnCommandLine(`SADDR=\`cat ~/Persistent/securedrop/install_files/ansible-base/app-sourcev3-ths\` &&  tor-browser $SADDR`);
        });
        
        let journalist = new PopupMenu.PopupMenuItem(_('Launch Journalist Interface'));
        journalist.connect('activate', () => {
            Util.trySpawnCommandLine(`JADDR=\`cut -d: f1 ~/Persistent/securedrop/install_files/ansible-base/app-journalist.auth_private\` &&  tor-browser "${JADDR}.onion"`);
        });
        
        let admin_label = new St.Label({
            text: _('Admin Actions'),
            y_expand: true,
            y_align: Clutter.ActorAlign.START,
        });
        
        let updates = new PopupMenu.PopupMenuItem(_('Check for SecureDrop Updates'));
        updates.connect('activate', () => {
            Util.trySpawnCommandLine(``);
        });
        
        let app_server_ssh = new PopupMenu.PopupMenuItem(_('SSH into the App Server'));
        app_server_ssh.connect('activate', () => {
            Util.trySpawnCommandLine(`gnome-terminal -- ssh app`);
        });
        
        let mon_server_ssh = new PopupMenu.PopupMenuItem(_('SSH into the Monitor Server'));
        mon_server_ssh.connect('activate', () => {
            Util.trySpawnCommandLine(`gnome-terminal -- ssh mon`);
        });
        
        let keypass = new PopupMenu.PopupMenuItem(_('Open KeePassXC Password Vault'));
        keypass.connect('activate', () => {
            Util.trySpawnCommandLine(`keepassxc`);
        });
        
        this.menu.addMenuItem(source);
        this.menu.addMenuItem(journalist);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        this.menu.addMenuItem(updates);
        this.menu.addMenuItem(app_server_ssh);
        this.menu.addMenuItem(mon_server_ssh);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        this.menu.addMenuItem(keypass);
    }
});

class Extension {
    constructor(uuid) {
        this._uuid = uuid;

        ExtensionUtils.initTranslations(GETTEXT_DOMAIN);
    }

    enable() {
        this._indicator = new Indicator();
        let pos = Main.sessionMode.panel.left.indexOf('appMenu');
        if ('apps-menu' in Main.panel.statusArea)
            pos++;
        Main.panel.addToStatusArea(this._uuid, this._indicator, pos, 'left');
    }

    disable() {
        this._indicator.destroy();
        this._indicator = null;
    }
}

function init(meta) {
    return new Extension(meta.uuid);
}
