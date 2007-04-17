# dictionary to hold the variables that can be set in the ccp1guirc file
global rc_vars 
rc_vars = {}
rc_vars['conn_scale'] = 1.0
rc_vars['conn_toler']   = 0.5
rc_vars['contact_scale'] = 1.0
rc_vars['contact_toler']   = 1.5
rc_vars['bg_rgb'] = (0,0,0)
rc_vars['pick_tolerance'] = 0.01
rc_vars['show_selection_by_colour'] = 1
rc_vars['field_line_width']  =  1
rc_vars['field_point_size']  =  2
# Molecule variables
rc_vars['mol_line_width']  =  3
rc_vars['mol_point_size']  =  4
rc_vars['mol_sphere_resolution'] = 8
rc_vars['mol_sphere_specular'] = 1.0
rc_vars['mol_sphere_diffuse'] = 1.0
rc_vars['mol_sphere_ambient'] = 0.4
rc_vars['mol_sphere_specular_power'] = 5
rc_vars['mol_cylinder_resolution'] = 8
rc_vars['mol_cylinder_specular'] = 0.7
rc_vars['mol_cylinder_diffuse'] = 0.7
rc_vars['mol_cylinder_ambient'] = 0.4
rc_vars['mol_cylinder_specular_power'] = 10
# Executable, script and directory locations
rc_vars['am1'] = None
rc_vars['chemsh_script_dir'] = None
# Stereo visulaisation
rc_vars['stereo'] = None
# Remember paths between restarts
rc_vars['old_path'] = 1
rc_vars['user_path'] = None
