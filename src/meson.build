pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'dynamic_wallpaper_editor')
gnome = import('gnome')

gnome.compile_resources('dynamic-wallpaper-editor',
	'dynamic-wallpaper-editor.gresource.xml',
	gresource_bundle: true,
	install: true,
	install_dir: pkgdatadir,
)

python3 = import('python3')

conf = configuration_data()
conf.set('PYTHON', python3.find_python().path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'dynamic-wallpaper-editor.in',
  output: 'dynamic-wallpaper-editor',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

dynamic_wallpaper_editor_sources = [
	'__init__.py',
	'gi_composites.py',
	'main.py',
	'window.py',
	'picture_row.py'
]

install_data(dynamic_wallpaper_editor_sources, install_dir: moduledir)
