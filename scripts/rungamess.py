
# run gamess-UK (foreground)
from ccp1gui.gamessuk import GAMESSUKCalc
from ccp1gui.zmatrix import Zmatrix, ZAtom
model = Zmatrix()

molecule = [ ( 'O', 0.0, 0.0, 0.0 ),
             ( 'H', 1.0, 0.0, 0.0 ),
             ( 'H', 0.0, 1.0, 0.0 ) ]

for a in molecule:
    symbol,x,y,z = a
    atom = ZAtom()
    atom.symbol = symbol
    atom.name = symbol
    atom.coord = [ x,y,z ]
    model.insert_atom(-1,atom)

model.list()

calc = GAMESSUKCalc()
calc.set_input('mol_obj',model)
calc.set_parameter('charge',1)
calc.set_parameter('job_name','water')
calc.set_parameter('spin',2)
calc.set_parameter('scf_method','Direct UHF')
calc.set_parameter('ana_homolumo',1)
calc.set_parameter('ana_homolumo1',1)
#calc.set_parameter('ana_orbitals',[3,4,5])
#calc.set_parameter('ana_potential',1)
#calc.set_parameter('ana_chargedengrad',1)
calc.set_parameter('ana_spinden',1)
job = calc.makejob(writeinput=1)
if job:
    job.run()
    job.tidy()
    #calc.summarise_results()
    for line in calc.get_output('log_file'):
        print line,
