project(
	'dynamic-wallpaper-editor',
	version: '2.6.0',
	meson_version: '>= 0.50.0',
)

i18n = import('i18n')

itstool = find_program('itstool')

subdir('data')
subdir('help')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
