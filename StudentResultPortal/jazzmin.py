# Admin Theme For DashBoard With The Images For Both Log In and Log Out

JAZZMIN_SETTINGS = {
    "custom_css": "css/my_jazzmin.css",  # Link to your custom CSS file
    "custom_js": "js/my_jazzmin.js",  # Path to your custom JS file

    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "Ecommerce Admin",

    # Title on the login screen (19 chars max)
    "site_header": "EMILIA",

    # Title on the brand (19 chars max)
    "site_brand": "EMILIA",

    # Logo to use for your site, must be present in static files
    "site_logo": "/img/GMMI_LOGO.png",

    

    # Logo to use for login form
    # "login_logo": "/img/3 copy.jpg",
    
    "site_logo_classes": "custom-logo-size",  # Use your custom class
    
    
    "custom_css": "css/my_jazzmin.css",  # Path to your custom CSS file
    "custom_js": "js/my_jazzmin.js",  # Path to your custom JS file


    # CSS classes that are applied to the logo above
    "site_logo_classes": "img-circle",

    # Welcome text on the login screen
    "welcome_sign": "Welcome to the EMILIA",
    

    # Copyright on the footer
    "copyright": "EMILIA Coorperation",
    
    
    
    # Search model
    "search_model": ["auth.User", "auth.Group"],

    # Field for user avatar
    "user_avatar": "profile.avatar",  # Assuming 'avatar' is the field name in your Profile model

    # Top Menu
    "topmenu_links": [
        {"name": "Home", "url": "/", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.User"},
        {"app": "books"},
    ],

    # User Menu Links
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.user"}
    ],

    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "books", "books.author", "books.book"],

    # Custom Links for Side Menu
    "custom_links": {
        "books": [{
            "name": "Make Messages",
            "url": "make_messages",
            "icon": "fas fa-comments",
            "permissions": ["books.view_book"]
        }]
    },

    # Custom Icons
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # Related Modal
    "related_modal_active": True,

    # UI Tweaks
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,

    # Change View
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
}

JAZZMIN_SETTINGS["show_ui_builder"] = True
