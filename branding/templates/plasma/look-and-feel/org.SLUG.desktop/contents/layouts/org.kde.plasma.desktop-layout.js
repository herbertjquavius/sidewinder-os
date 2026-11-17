// $name default desktop: one floating bottom panel, games pinned up front

// Wallpaper on every desktop
var desktops = desktopsForActivity(currentActivity());
for (var i = 0; i < desktops.length; i++) {
    desktops[i].wallpaperPlugin = "org.kde.image";
    desktops[i].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktops[i].writeConfig("Image", "file:///usr/share/wallpapers/$slug/");
}

var panel = new Panel;
panel.location = "bottom";
panel.height = 2 * Math.ceil(gridUnit * 2.5 / 2);
panel.floating = true;

// App menu opens from our logo
var launcher = panel.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "$slug");
launcher.currentConfigGroup = ["Shortcuts"];
launcher.writeConfig("global", "Alt+F1");

// Pinned apps, games first
var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:com.valvesoftware.Steam.desktop",
    "applications:com.heroicgameslauncher.hgl.desktop",
    "applications:net.lutris.Lutris.desktop",
    "applications:$slug-shorts.desktop",
    "applications:org.mozilla.firefox.desktop",
    "applications:com.discordapp.Discord.desktop",
    "applications:org.kde.dolphin.desktop",
    "applications:$slug-welcome.desktop"
]);

panel.addWidget("org.kde.plasma.marginsseparator");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");
panel.addWidget("org.kde.plasma.showdesktop");
