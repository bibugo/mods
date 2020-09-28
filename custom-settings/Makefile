include $(TOPDIR)/rules.mk

PKG_NAME:=custom-settings
PKG_RELEASE:=1
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=mods
	CATEGORY:=+ Mods
	TITLE:=Custom Settings
	DEPENDS:=
endef

define Build/Prepare
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/custom-settings $(1)/etc/uci-defaults/99-custom-settings
	$(INSTALL_DIR) $(1)/etc/hotplug.d/iface/
	$(INSTALL_CONF) ./files/01-dhcp-fallback $(1)/etc/hotplug.d/iface/01-dhcp-fallback
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
