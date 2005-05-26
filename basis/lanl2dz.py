#
#    This file is part of the CCP1 Graphical User Interface (ccp1gui)
# 
#   (C) 2002-2005 CCLRC Daresbury Laboratory
# 
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
"""Sample ECP basis module, with ecp and basis definitions held inline
"""
import basis

def valid_elements():
    """Return list of elements supported by this file """
    return ['cl', 'br']

def get_ecp(element):
    """Return ecp for a given element"""
    p = None
    if element == 'cl':
        p = basis.AtomECP(z=17,name='lan2dz')
        p.load_from_list([ [2, 10],
                           [2, "d potential",
                            [1 ,     -10.00000000,     94.81300000 ] ,
                            [2 ,      66.27291700,    165.64400000 ] ,
                            [2 ,     -28.96859500,     30.83170000 ] ,
                            [2 ,     -12.86633700,     10.58410000 ] ,
                            [2 ,      -1.71021700,      3.77040000 ] ] ,
                           [0, "s-d potential",
                            [0 ,       3.00000000,    128.83910000 ] ,
                            [1 ,      12.85285100,    120.37860000 ] ,
                            [2 ,     275.67239800,     63.56220000 ] ,
                            [2 ,     115.67771200,     18.06950000 ] ,
                            [2 ,      35.06060900,      3.81420000 ] ] ,
                           [1, "p-d potential",
                            [0 ,       5.00000000,    216.52630000 ] ,
                            [1 ,       7.47948600,     46.57230000 ] ,
                            [2 ,     613.03200000,    147.46850000 ] ,
                            [2 ,     280.80068500,     48.98690000 ] ,
                            [2 ,     107.87882400,     13.20960000 ] ,
                            [2 ,      15.34395600,      3.18310000 ] ] ])

    elif element == 'br':
        p = basis.AtomECP(z=35,name='lan2dz')
        p.load_from_list([ [3, 28],
                           [3, "f potential",
                            [1, 213.6143969, -28.0000000] ,
                            [2, 41.0585380, -134.9268852],
                            [2, 8.7086530, -41.9271913],
                            [2, 2.6074661, -5.9336420]],
                           [0, "s-f potential",
                            [0, 54.1980682, 3.0000000],
                            [1, 32.9053558, 27.3430642],
                            [2, 13.6744890, 118.8028847],
                            [2, 3.0341152, 43.4354876]],
                           [1, "p-f potential",
                            [0, 54.2563340, 5.0000000] ,
                            [1, 26.0095593, 25.0504252],
                            [2, 28.2012995, 92.6157463],
                            [2, 9.4341061, 95.8249016],
                            [2, 2.5321764, 26.2684983]],
                           [2, "d-f potential",
                            [0, 87.6328721, 3.0000000],
                            [1, 61.7373377, 22.5533557],
                            [2, 32.4385104, 178.1241988],
                            [2, 8.7537199, 76.9924162],
                            [2, 1.6633189, 9.4818270]]])
        return p

def get_basis(element):
    """Return basis set for a given element"""
    p=None
    if element == 'cl':
        p = basis.AtomBasis(z=17,name='lanl2dz')
        p.load_from_list([['S', [2.23100000, -0.49005890   ],
                                [0.47200000, 1.25426840  ] ],
                          ['S', [0.16310000, 1.00000000  ]],
                          ['P', [6.29600000,  -0.06356410  ],
                                [0.63330000, 1.01413550  ]],
                          ['P', [0.18190000,  1.00000000  ]]])
    elif element == 'br':
        p = basis.AtomBasis(z=35,name='lanl2dz')
        p.load_from_list([['S', [1.1590, -3.0378769 ],
                                [0.7107, 3.3703735 ]],
                          ['S', [0.1905, 1.000000 ]],
                          ['P', [2.6910, -0.1189800 ],
                                [0.4446, 1.0424471 ]],
                          ['P', [0.1377, 1.0000000 ]]])
    return p

