include $(TOPDIR)/rules.mk

PKG_NAME:=neo2-oled
PKG_VERSION:=0.1-rpi-gpio-np-0.6.3-1
PKG_RELEASE:=1
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=mods
	CATEGORY:=+ Mods
	TITLE:=Nano Pi Neo2 OLED script
	DEPENDS:=+python
endef

define Build/Prepare
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/etc/modules.d/
	$(INSTALL_CONF) ./files/i2c-gpio-custom $(1)/etc/modules.d/59-i2c-gpio-custom

	$(INSTALL_DIR) $(1)/usr/lib/python2.7/site-packages/
	$(INSTALL_DATA) ./files/RPi.GPIO-0.6.3-py2.7.egg-info $(1)/usr/lib/python2.7/site-packages/
	$(INSTALL_DIR) $(1)/usr/lib/python2.7/site-packages/RPi/
	$(INSTALL_BIN) ./files/RPi/_GPIO.so $(1)/usr/lib/python2.7/site-packages/RPi/
	$(INSTALL_DATA) ./files/RPi/__init__.py $(1)/usr/lib/python2.7/site-packages/RPi/
	$(INSTALL_DIR) $(1)/usr/lib/python2.7/site-packages/RPi/GPIO/
	$(CP) ./files/RPi/GPIO/* $(1)/usr/lib/python2.7/site-packages/RPi/GPIO/

	$(INSTALL_DIR) $(1)/usr/share/oled/
	$(CP) ./files/oled/* $(1)/usr/share/oled/

	$(INSTALL_DIR) $(1)/etc/init.d/
	$(INSTALL_BIN) ./files/oled.init $(1)/etc/init.d/oled
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
