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
"""Element data, including colours, radii, masses and
code to construct a periodic table as a Pmw widget.
"""

# Colours - list indexed by Z

rgb_min = 0
rgb_max = 106

colours = [
(.8   ,.8   , .8),
(0.549,0.549,0.706) ,
(0.706,0.706,0.706) ,
(0.51,0.353,0.118) ,
(0.353,0.51,0.118) ,
(0.314,0.706,0.706) ,
(0.0,0.627,0.0) ,
(0.235,0.235,0.588) ,
(0.627,0.0,0.0) ,
(0.0,0.627,0.627) ,
(0.706,0.706,0.706) ,
(0.51,0.353,0.118) ,
(0.353,0.51,0.118) ,
(0.392,0.392,0.588) ,
(0.235,0.235,0.235) ,
(0.471,0.392,0.039) ,
(0.431,0.471,0.118) ,
(0.039,0.412,0.471) ,
(0.706,0.706,0.706) ,
(0.51,0.353,0.118) ,
(0.353,0.51,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.706,0.706,0.118) ,
(0.392,0.392,0.588) ,
(0.235,0.235,0.235) ,
(0.471,0.392,0.039) ,
(0.431,0.471,0.118) ,
(0.039,0.412,0.471) ,
(0.706,0.706,0.706) ,
(0.51,0.353,0.118) ,
(0.353,0.51,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.431,0.431,0.118) ,
(0.392,0.392,0.588) ,
(0.353,0.353,0.353) ,
(0.471,0.392,0.039) ,
(0.431,0.471,0.118) ,
(0.039,0.412,0.471) ,
(0.706,0.706,0.706) ,
(0.51,0.353,0.118) ,
(0.353,0.51,0.118) ,
(0.588,0.588,0.118) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.039,0.412,0.039) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.588,0.588,0.118) ,
(0.392,0.392,0.588) ,
(0.353,0.353,0.353) ,
(0.471,0.392,0.039) ,
(0.431,0.471,0.118) ,
(0.039,0.412,0.471) ,
(0.706,0.706,0.706) ,
(0.51,0.353,0.118) ,
(0.353,0.51,0.118) ,
(0.706,0.706,0.118) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039) ,
(0.471,0.392,0.039),
(0.471,0.392,0.039),
(0.9,0.9,0.9),
(0.9,0.9,0.9),
(0.7,0.0,0.7) ]

# Mapping Z to element
z_to_el = { 
1   : 'H'  ,
2   : 'He' ,
3   : 'Li' ,
4   : 'Be' ,
5   : 'B'  ,
6   : 'C'  ,
7   : 'N'  ,
8   : 'O'  ,
9   : 'F'  ,
10   : 'Ne' ,
11   : 'Na' ,
12   : 'Mg' ,
13   : 'Al' ,
14   : 'Si' ,
15   : 'P'  ,
16   : 'S'  ,
17   : 'Cl' ,
18   : 'Ar' ,
19   : 'K'  ,
20   : 'Ca' ,
21   : 'Sc' ,
22   : 'Ti' ,
23   : 'V'  ,
24   : 'Cr' ,
25   : 'Mn' ,
26   : 'Fe' ,
27   : 'Co' ,
28   : 'Ni' ,
29   : 'Cu' ,
30   : 'Zn' ,
31   : 'Ga' ,
32   : 'Ge' ,
33   : 'As' ,
34   : 'Se' ,
35   : 'Br' ,
36   : 'Kr' ,
37   : 'Rb' ,
38   : 'Sr' ,
39   : 'Y'  ,
40   : 'Zr' ,
41   : 'Nb' ,
42   : 'Mo' ,
43   : 'Tc' ,
44   : 'Ru' ,
45   : 'Rh' ,
46   : 'Pd' ,
47   : 'Ag' ,
48   : 'Cd' ,
49   : 'In' ,
50   : 'Sn' ,
51   : 'Sb' ,
52   : 'Te' ,
53   : 'I'  ,
54   : 'Xe' ,
55   : 'Cs' ,
56   : 'Ba' ,
57   : 'La' ,
58   : 'Ce' ,
59   : 'Pr' ,
60   : 'Nd' ,
61   : 'Pm' ,
62   : 'Sm' ,
63   : 'Eu' ,
64   : 'Gd' ,
65   : 'Tb' ,
66   : 'Dy' ,
67   : 'Ho' ,
68   : 'Er' ,
69   : 'Tm' ,
70   : 'Yb' ,
71   : 'Lu' ,
72   : 'Hf' ,
73   : 'Ta' ,
74   : 'W'  ,
75   : 'Re' ,
76   : 'Os' ,
77   : 'Ir' ,
78   : 'Pt' ,
79   : 'Au' ,
80   : 'Hg' ,
81   : 'Tl' ,
82   : 'Pb' ,
83   : 'Bi' ,
84   : 'Po' ,
85   : 'At' ,
86   : 'Rn' ,
87   : 'Fr' ,
88   : 'Ra' ,
89   : 'Ac' ,
90   : 'Th' ,
91   : 'Pa' ,
92   : 'U'  ,
93   : 'Np' ,
94   : 'Pu' ,
95   : 'Am' ,
96   : 'Cm' ,
97   : 'Bk' ,
98   : 'Cf' ,
99   : 'Es' ,
100   : 'Fm' ,
101   : 'Md' ,
102   : 'No' ,
103   : 'Lr' ,
104   : 'Unq',
105   : 'Unp', 
106   : 'XX',
107   : 'XY', }


# mapping symbols to Z
sym2no = {
'h'  : 1,
'he' : 2,
'li' : 3,
'be' : 4,
'b'  : 5,
'c'  : 6,
'n'  : 7,
'o'  : 8,
'f'  : 9,
'ne' : 10,
'na' : 11,
'mg' : 12,
'al' : 13,
'si' : 14,
'p'  : 15,
's'  : 16,
'cl' : 17,
'ar' : 18,
'k'  : 19,
'ca' : 20,
'sc' : 21,
'ti' : 22,
'v'  : 23,
'cr' : 24,
'mn' : 25,
'fe' : 26,
'co' : 27,
'ni' : 28,
'cu' : 29,
'zn' : 30,
'ga' : 31,
'ge' : 32,
'as' : 33,
'se' : 34,
'br' : 35,
'kr' : 36,
'rb' : 37,
'sr' : 38,
'y'  : 39,
'zr' : 40,
'nb' : 41,
'mo' : 42,
'tc' : 43,
'ru' : 44,
'rh' : 45,
'pd' : 46,
'ag' : 47,
'cd' : 48,
'in' : 49,
'sn' : 50,
'sb' : 51,
'te' : 52,
'i'  : 53,
'xe' : 54,
'cs' : 55,
'ba' : 56,
'la' : 57,
'ce' : 58,
'pr' : 59,
'nd' : 60,
'pm' : 61,
'sm' : 62,
'eu' : 63,
'gd' : 64,
'tb' : 65,
'dy' : 66,
'ho' : 67,
'er' : 68,
'tm' : 69,
'yb' : 70,
'lu' : 71,
'hf' : 72,
'ta' : 73,
'w'  : 74,
're' : 75,
'os' : 76,
'ir' : 77,
'pt' : 78,
'au' : 79,
'hg' : 80,
'tl' : 81,
'pb' : 82,
'bi' : 83,
'po' : 84,
'at' : 85,
'rn' : 86,
'fr' : 87,
'ra' : 88,
'ac' : 89,
'th' : 90,
'pa' : 91,
'u'  : 92,
'np' : 93,
'pu' : 94,
'am' : 95,
'cm' : 96,
'bk' : 97,
'cf' : 98,
'es' : 99,
'fm' : 100,
'md' : 101,
'no' : 102,
'lr' : 103,
'H'  : 1,
'He' : 2,
'Li' : 3,
'Be' : 4,
'B'  : 5,
'C'  : 6,
'N'  : 7,
'O'  : 8,
'F'  : 9,
'Ne' : 10,
'Na' : 11,
'Mg' : 12,
'Al' : 13,
'Si' : 14,
'P'  : 15,
'S'  : 16,
'Cl' : 17,
'Ar' : 18,
'K'  : 19,
'Ca' : 20,
'Sc' : 21,
'Ti' : 22,
'V'  : 23,
'Cr' : 24,
'Mn' : 25,
'Fe' : 26,
'Co' : 27,
'Ni' : 28,
'Cu' : 29,
'Zn' : 30,
'Ga' : 31,
'Ge' : 32,
'As' : 33,
'Se' : 34,
'Br' : 35,
'Kr' : 36,
'Rb' : 37,
'Sr' : 38,
'Y'  : 39,
'Zr' : 40,
'Nb' : 41,
'Mo' : 42,
'Tc' : 43,
'Ru' : 44,
'Rh' : 45,
'Pd' : 46,
'Ag' : 47,
'Cd' : 48,
'In' : 49,
'Sn' : 50,
'Sb' : 51,
'Te' : 52,
'I'  : 53,
'Xe' : 54,
'Cs' : 55,
'Ba' : 56,
'La' : 57,
'Ce' : 58,
'Pr' : 59,
'Nd' : 60,
'Pm' : 61,
'Sm' : 62,
'Eu' : 63,
'Gd' : 64,
'Tb' : 65,
'Dy' : 66,
'Ho' : 67,
'Er' : 68,
'Tm' : 69,
'Yb' : 70,
'Lu' : 71,
'Hf' : 72,
'Ta' : 73,
'W'  : 74,
'Re' : 75,
'Os' : 76,
'Ir' : 77,
'Pt' : 78,
'Au' : 79,
'Hg' : 80,
'Tl' : 81,
'Pb' : 82,
'Bi' : 83,
'Po' : 84,
'At' : 85,
'Rn' : 86,
'Fr' : 87,
'Ra' : 88,
'Ac' : 89,
'Th' : 90,
'Pa' : 91,
'U'  : 92,
'Np' : 93,
'Pu' : 94,
'Am' : 95,
'Cm' : 96,
'Bk' : 97,
'Cf' : 98,
'Es' : 99,
'Fm' : 100,
'Md' : 101,
'No' : 102,
'Lr' : 103,
'Unq' : 104,
'Unp' : 105,
# Use 106 to display selected atoms
'Zz'  : 106,
'zz'  : 106,
'X'  : 0,
'x'  : 0,
'Bq'  : -1,
'bq'  : -1,
}

# Row and Column indices for drawing the periodic table
rc = { 
'H'  : (1,1),
'He' : (1,18),
'Li' : (2,1),
'Be' : (2,2),
'B'  : (2,13),
'C'  : (2,14),
'N'  : (2,15),
'O'  : (2,16),
'F'  : (2,17),
'Ne' : (2,18),
'Na' : (3,1),
'Mg' : (3,2),
'Al' : (3,13),
'Si' : (3,14),
'P'  : (3,15),
'S'  : (3,16),
'Cl' : (3,17),
'Ar' : (3,18),
'K'  : (4,1),
'Ca' : (4,2),
'Sc' : (4,3),
'Ti' : (4,4),
'V'  : (4,5),
'Cr' : (4,6),
'Mn' : (4,7),
'Fe' : (4,8),
'Co' : (4,9),
'Ni' : (4,10),
'Cu' : (4,11),
'Zn' : (4,12),
'Ga' : (4,13),
'Ge' : (4,14),
'As' : (4,15),
'Se' : (4,16),
'Br' : (4,17),
'Kr' : (4,18),
'Rb' : (5,1),
'Sr' : (5,2),
'Y'  : (5,3),
'Zr' : (5,4),
'Nb' : (5,5),
'Mo' : (5,6),
'Tc' : (5,7),
'Ru' : (5,8),
'Rh' : (5,9),
'Pd' : (5,10),
'Ag' : (5,11),
'Cd' : (5,12),
'In' : (5,13),
'Sn' : (5,14),
'Sb' : (5,15),
'Te' : (5,16),
'I'  : (5,17),
'Xe' : (5,18),
'Cs' : (6,1),
'Ba' : (6,2),
'La' : (6,3),
'Ce' : (8,5),
'Pr' : (8,6),
'Nd' : (8,7),
'Pm' : (8,8),
'Sm' : (8,9),
'Eu' : (8,10),
'Gd' : (8,11),
'Tb' : (8,12),
'Dy' : (8,13),
'Ho' : (8,14),
'Er' : (8,15),
'Tm' : (8,16),
'Yb' : (8,17),
'Lu' : (8,18),
'Hf' : (6,4),
'Ta' : (6,5),
'W'  : (6,6),
'Re' : (6,7),
'Os' : (6,8),
'Ir' : (6,9),
'Pt' : (6,10),
'Au' : (6,11),
'Hg' : (6,12),
'Tl' : (6,13),
'Pb' : (6,14),
'Bi' : (6,15),
'Po' : (6,16),
'At' : (6,17),
'Rn' : (6,18),
'Fr' : (7,1),
'Ra' : (7,2),
'Ac' : (7,3),
'Th' : (9,5),
'Pa' : (9,6),
'U'  : (9,7),
'Np' : (9,8),
'Pu' : (9,9),
'Am' : (9,10),
'Cm' : (9,11),
'Bk' : (9,12),
'Cf' : (9,13),
'Es' : (9,14),
'Fm' : (9,15),
'Md' : (9,16),
'No' : (9,17),
'Lr' : (9,18),
'Unq': (7,4),
'Unp': (7,5),
'Unh': (7,6) }


# the display table (aus)
# H=.7 is just for appearance
#
#
# note that indexing with -1 accesses the last element (0.4 copied at start and edn)
#
rcov = [
0.4,
0.7,                                   3.80,    
2.76,1.99,                1.62,1.33,1.23,1.14,0.95,3.80,
3.42,2.85,                2.38,2.09,1.90,1.90,1.90,3.80,
4.18,3.42,
     3.04,2.66,2.57,2.66,2.66,2.66,2.57,2.57,2.57,2.57,
                          2.47,2.38,2.18,2.18,2.18,3.80,
4.46,3.80,               
     3.42,2.94,2.76,2.76,2.57,2.47,2.57,2.66,3.04,2.94,
                          2.94,2.76,2.76,2.66,2.66,3.80,
4.94,4.09,
     3.71,
     3.52,3.52,3.52,3.52,3.52,3.52,3.42,3.33,3.33,3.33,3.33,3.33,3.33,3.33,
          2.94,2.76,2.57,2.57,2.47,2.57,2.57,2.57,2.85,
                         3.61,3.42,3.04,3.61,3.61,3.80,
4.94,4.09,
     3.71,
     3.42,3.42,3.33,3.33,3.33,3.33,3.23,3.13,3.13,3.13,3.13,3.13,3.13,3.13, 1., 1., 1.,1.,1.,1., 0.4,]
     

# joe lennards table angstroms
# 1.0 added as index [0] and [-1] see above
rvdw = [  1.0,
  1.20,                              1.40,
  1.82,1.78,1.74,1.70,1.55,1.52,1.47,1.54,
  2.27,2.22,2.16,2.10,1.80,1.80,1.75,1.88,
  2.75,2.57,
       2.56,2.54,2.52,2.50,2.48,2.46,2.44,2.42,2.41,2.40,
            2.40,2.10,1.85,1.90,1.85,2.02,
  3.10,2.80,
       2.77,2.74,2.71,2.68,2.65,2.62,2.59,2.56,2.53,2.51,
            2.50,2.20,2.10,2.06,1.98,2.16, 1., 1., 1.]

# double check these values...
#hvd values obtained from http://www.webelements.com/ and recorded to their
#    known accuracy.

atomic_mass = {
   'H'  :   1.00794,
   'He' :   4.002602,
   'HE' :   4.002602,
   'Li' :   6.941,
   'LI' :   6.941,
   'Be' :   9.012182,
   'BE' :   9.012182,
   'B'  :  10.811,
   'C'  :  12.0107,
   'N'  :  14.0067,
   'O'  :  15.9994,
   'F'  :  18.9984032,
   'Ne' :  20.1797,
   'NE' :  20.1797,
   'Na' :  22.989770,
   'NA' :  22.989770,
   'Mg' :  24.3050,
   'MG' :  24.3050,
   'Al' :  26.981538,
   'AL' :  26.981538,
   'Si' :  28.0855,
   'SI' :  28.0855,
   'P'  :  30.973761,
   'S'  :  32.065,
   'Cl' :  35.453,
   'CL' :  35.453,
   'Ar' :  39.948,
   'AR' :  39.948,
   'K'  :  39.0983,
   'Ca' :  40.078,
   'CA' :  40.078,
   'Sc' :  44.955910,
   'SC' :  44.955910,
   'Ti' :  47.867,
   'TI' :  47.867,
   'V'  :  50.9415,
   'Cr' :  51.9961,
   'CR' :  51.9961,
   'Mn' :  54.938049,
   'MN' :  54.938049,
   'Fe' :  55.845,
   'FE' :  55.845,
   'Co' :  58.933200,
   'CO' :  58.933200,
   'Ni' :  58.6934,
   'NI' :  58.6934,
   'Cu' :  63.546,
   'CU' :  63.546,
   'Zn' :  65.39,
   'ZN' :  65.39,
   'Ga' :  69.723,
   'GA' :  69.723,
   'Ge' :  72.64,
   'GE' :  72.64,
   'As' :  74.92160,
   'AS' :  74.92160,
   'Se' :  78.96,
   'SE' :  78.96,
   'Br' :  79.904,
   'BR' :  79.904,   
   'Kr' :  83.80,
   'KR' :  83.80,
   'Rb' :  85.4678,
   'RB' :  85.4678,
   'Sr' :  87.62,
   'SR' :  87.62,
   'Y'  :  88.90585,
   'Zr' :  91.224,
   'ZR' :  91.224,
   'Nb' :  92.90638,
   'NB' :  92.90638,
   'Mo' :  95.94,
   'MO' :  95.94,
   'Tc' :  98,
   'TC' :  98,
   'Ru' : 101.07,
   'RU' : 101.07,
   'Rh' : 102.90550,
   'RH' : 102.90550,
   'Pd' : 106.42,
   'PD' : 106.42,
   'Ag' : 107.8682,
   'AG' : 107.8682,
   'Cd' : 112.411,
   'CD' : 112.411,
   'In' : 114.818,
   'IN' : 114.818,
   'Sn' : 118.710,
   'SN' : 118.710,
   'Sb' : 121.760,
   'SB' : 121.760,
   'Te' : 127.60,
   'TE' : 127.60,
   'I'  : 126.90447,
   'Xe' : 131.293,
   'XE' : 131.293,
   'Cs' : 132.90545,
   'CS' : 132.90545,
   'Ba' : 137.327,
   'BA' : 137.327,
   'La' : 138.9055,
   'LA' : 138.9055,
   'Ce' : 140.116,
   'CE' : 140.116,
   'Pr' : 140.90765,
   'PR' : 140.90765,
   'Nd' : 144.24,
   'ND' : 144.24,
   'Pm' : 145,
   'PM' : 145,
   'Sm' : 150.36,
   'SM' : 150.36,
   'Eu' : 151.964,
   'EU' : 151.964,
   'Gd' : 157.25,
   'GD' : 157.25,
   'Tb' : 158.92534,
   'TB' : 158.92534,
   'Dy' : 162.50,
   'DY' : 162.50,
   'Ho' : 164.93032,
   'HO' : 164.93032,
   'Er' : 167.259,
   'ER' : 167.259,
   'Tm' : 168.93421,
   'TM' : 168.93421,
   'Yb' : 173.04,
   'YB' : 173.04,
   'Lu' : 174.967,
   'LU' : 174.967,
   'Hf' : 178.49,
   'HF' : 178.49,
   'Ta' : 180.9479,
   'TA' : 180.9479,
   'W'  : 183.84,
   'Re' : 186.207,
   'RE' : 186.207,
   'Os' : 190.23,
   'OS' : 190.23,
   'Ir' : 192.217,
   'IR' : 192.217,
   'Pt' : 195.078,
   'PT' : 195.078,
   'Au' : 196.96655,
   'AU' : 196.96655,
   'Hg' : 200.59,
   'HG' : 200.59,
   'Tl' : 204.3833,
   'TL' : 204.3833,
   'Pb' : 207.2,
   'PB' : 207.2,
   'Bi' : 208.98038,
   'BI' : 208.98038,
   'Po' : 208.98,
   'PO' : 208.98,
   'At' : 209.99,
   'AT' : 209.99,
   'Rn' : 222.02,
   'RN' : 222.02,
   'Fr' : 223.02,
   'FR' : 223.02,
   'Ra' : 226.03,
   'RA' : 226.03,
   'Ac' : 227.03,
   'AC' : 227.03,
   'Th' : 232.0381,
   'TH' : 232.0381,
   'Pa' : 231.03588,
   'PA' : 231.03588,
   'U'  : 238.02891,
   'Np' : 237.05,
   'NP' : 237.05,
   'Pu' : 244.06,
   'PU' : 244.06,
   'Am' : 243.06,
   'AM' : 243.06,
   'Cm' : 247.07,
   'CM' : 247.07,
   'Bk' : 247.07,
   'BK' : 247.07,
   'Cf' : 251.08,
   'CF' : 251.08,
   'Es' : 252.08,
   'ES' : 252.08,
   'Fm' : 257.10,
   'FM' : 257.10,
   'Md' : 258.10,
   'MD' : 258.10,
   'No' : 259.10,
   'NO' : 259.10,
   'Lr' : 262.11,
   'LR' : 262.11,
   'Rf' : 261.11,
   'RF' : 261.11,
   'Db' : 262.11,
   'DB' : 262.11,
   'Sg' : 266.12,
   'SG' : 266.12,
   'Bh' : 264.12,
   'BH' : 264.12,
   'Hs' : 269.13,
   'HS' : 269.13,
   'Mt' : 268.14,
   'MT' : 268.14,
}

"""
# Characteristic lengths of single bonds.
# Reference: CRC Handbook of Chemistry and Physics, 87th edition, (2006), Sec. 9 p. 46
   As   Br   C    Cl   F    Ge   H    I    N    O    P    S    Sb   Se   Si
As 2.10
Br 2.32 2.28
C  1.96 1.94 1.53
Cl 2.17 2.14 1.79 1.99
F  1.71 1.76 1.39 1.63 1.41
Ge	2.30 1.95 2.15 1.73 2.40
H  1.51 1.41 1.09 1.28 0.92 1.53 0.74
I	2.47 2.13 2.32 1.91 2.51 1.61 2.67
N	     1.46 1.90 1.37	 1.02	   1.45
O	     1.42 1.70 1.42	 0.96	   1.43 1.48
P       2.22 1.85 2.04 1.57	 1.42	   1.65      2.25
S       2.24 1.82 2.05 1.56	 1.34                     2.00
Sb	          2.33           1.70
Se           1.95      1.71      1.47                               2.33
Si      2.21 1.87 2.05 1.58      1.48 2.44      1.63      2.14           2.33
Sn           2.14 2.28           1.71 2.67
Te                     1.82      1.66
"""

# REM - symbols should be in lower case!
bond_lengths = {}
bond_lengths['as'] = { 'as' : 2.10,
                       'br' : 2.32,
                       'c'  : 1.96,
                       'cl' : 2.17,
                       'f'  : 1.71,
                       'h'  : 1.51 }
                       
bond_lengths['br'] = { 'br': 2.28,
                       'c' : 1.94,
                       'cl': 2.14,
                       'f' : 1.76,
                       'ge': 2.30,
                       'h' : 1.41,
                       'i' : 2.47,
                       'p' : 2.22,
                       's' : 2.24,
                       'si' : 2.21 }

bond_lengths['c'] = { 'c' : 1.53,
                      'cl': 1.79,
                      'f' : 1.39,
                      'ge': 1.95,
                      'h' : 1.09,
                      'i' : 2.13,
                      'n' : 1.46,
                      'o' : 1.42,
                      'p' : 1.85,
                      's' : 1.82,
                      'se': 1.95,
                      'si': 1.87,
                      'sn': 2.14 }

bond_lengths['cl'] = { 'cl' : 1.99,
                       'f'  : 1.63,
                       'ge' : 2.15,
                       'h'  : 1.28,
                       'i'  : 2.32,
                       'n'  : 1.90,
                       'o'  : 1.70,
                       'p'  : 2.04,
                       's'  : 2.05,
                       'sb' : 2.33,
                       'si' : 2.05,
                       'sn' : 2.28 }

bond_lengths['f'] = { 'f'  : 1.41,
                      'ge' : 1.73,
                      'h'  : 0.92,
                      'i'  : 1.91,
                      'n'  : 1.37,
                      'o'  : 1.42,
                      'p'  : 1.57,
                      's'  : 1.56,
                      'se' : 1.71,
                      'si' : 1.58,
                      'te' : 1.82 }

bond_lengths['ge'] = { 'ge' : 2.40,
                       'h'  : 1.53,
                       'i'  : 2.51 }
                       
bond_lengths['h'] = { 'h' : 0.74,
                      'i' : 1.61,
                      'n' : 1.02,
                      'o' : 0.96,
                      'p' : 1.42,
                      's' : 1.34,
                      'sb': 1.70,
                      'se': 1.47,
                      'si': 1.48,
                      'sn': 1.71,
                      'te': 1.66 }

bond_lengths['i'] = { 'i'  : 2.67,
                      'si' : 2.44,
                      'sn' : 2.67 }

bond_lengths['n'] = { 'n' : 1.45,
                      'o' : 1.43,
                      'p' : 1.65 }

bond_lengths['o'] = { 'o'  : 1.48,
                      'si' : 1.63 }

bond_lengths['p'] = { 'p' : 2.25 }

bond_lengths['s'] = { 's' : 2.00 }

bond_lengths['se'] = { 'se' : 2.33 }

bond_lengths['si'] = { 'si' : 2.33 }

def get_bond_length( symbol1,symbol2 ):
    """ Get the characteristic lengths of single bonds as defined in:
        Reference: CRC Handbook of Chemistry and Physics, 87th edition, (2006), Sec. 9 p. 46
        If we can't find one return 1.0 as a default 
    """
    global bond_lengths

    symbol1 = symbol1.lower()
    symbol2 = symbol2.lower()

    #print "Getting bond length for %s-%s" % ( symbol1, symbol2 )

    if bond_lengths.has_key( symbol1 ):
        if bond_lengths[ symbol1 ].has_key( symbol2 ):
            return bond_lengths[ symbol1 ][ symbol2 ]
        
    if bond_lengths.has_key( symbol2 ):
        if bond_lengths[ symbol2 ].has_key( symbol1 ):
            return bond_lengths[ symbol2 ][ symbol1 ]
    
    print 'No data for bond length for %s-%s' % (symbol1,symbol2)
    return 1.0

# Get atom symbol from the name
import string,re
def name_to_element( name ):
    """ Determine the element type of an atom from its name, e.g. Co_2b -> Co
    """

    # Determine the element from the first 2 chars of the name
    if ( len( name ) == 1 ):
        if not re.match( '[a-zA-Z]', name ):
            print "Error converting name to symbol for atom %s!" % name
            element = 'XX'
        else:
            element = name
    else:
        # See if 2nd char is a character - if so use 1st 2 chars as symbol
        if re.match( '[a-zA-Z]', name[1] ):
            element = name[0:2]
        else:
            element = name[0]

    element = string.capitalize( element )
    return element

    
try:
    from Tkinter import *
    import Pmw
    class PeriodicTable(Pmw.MegaWidget):
    
        """ A Megawidget displaying the periodic table
        this version uses buttons for each atom which invoke the
        command provided with the atomic number as an argument
        """
     
        def __init__(self, parent = None, **kw):
    
            # Define the megawidget options.
            optiondefs = (
    	    ('command',   None,   Pmw.INITOPT),
            )
            self.defineoptions(kw, optiondefs)
    
            # Initialise base class (after defining options).
            Pmw.MegaWidget.__init__(self, parent)
    
            # Create the components.
            interior = self.interior()
    
            self.f1 = Frame(parent)
     
            self.buttons = []
            for i in range(1,104):
                # Create the scale component.
                el = z_to_el[i]
                r,c = rc[el]
                red,green,blue=colours[i]
                fac = 0.4
                #print red,green,blue
                red   = 1.0 - (1.0 - red)*fac
                green = 1.0 - (1.0 - green)*fac
                blue  = 1.0 - (1.0 - blue)*fac
                tk_rgb = "#%02x%02x%02x" % (255*red, 255*green, 255*blue)
                #print 'mod',red,green,blue,tk_rgb
                t = self.createcomponent('button-'+str(i),
                                         (), None,
                                         Button, self.f1,
                                         background=tk_rgb,
                                         command = lambda s=self,z=i : s.press(z),
                                         height=1,
                                         width=3,
                                         text=el)
                #t.place(relx=float(r)/9,rely=float(c)/18,relheight=1.0/10.0,relwidth=1.0/19.0)
                t.grid(row=r,column=c)
                self.buttons.append(t)
    
            t = self.createcomponent('toggle-mini',
                                         (), None,
                                         Button, self.f1,
                                         background=tk_rgb,
                                         command = self.mini,
                                         height=1,
                                         text='Short Table')
            t.grid(row=1,column=5,columnspan=3)
    
            self.f2 = Frame(parent)
     
            self.buttons = []
            count = 1
            for i in [1,3,6,7,8,11,12,14,15,16,17,35,53]:
                el = z_to_el[i]
                red,green,blue=colours[i]
                fac = 0.4
                #print red,green,blue
                red   = 1.0 - (1.0 - red)*fac
                green = 1.0 - (1.0 - green)*fac
                blue  = 1.0 - (1.0 - blue)*fac
                tk_rgb = "#%02x%02x%02x" % (255*red, 255*green, 255*blue)
                #print 'mod',red,green,blue,tk_rgb
                t = self.createcomponent('mini-button-'+str(i),
                                         (), None,
                                         Button, self.f2,
                                         background=tk_rgb,
                                         command = lambda s=self,z=i : s.press(z),
                                         height=1,
                                         width=3,
                                         text=el)
                #t.place(relx=float(r)/9,rely=float(c)/18,relheight=1.0/10.0,relwidth=1.0/19.0)
                t.pack(side='left')
    
            t = self.createcomponent('toggle-maxi',
                                     (), None,
                                     Button, self.f2,
                                     background=tk_rgb,
                                     command = self.maxi,
                                     height=1,
                                     text='More..')
    
            t.pack(side='left')
            self.f2.pack()
    
        def maxi(self):
            self.f2.forget()
            self.f1.pack()
    
        def mini(self):
            self.f1.forget()
            self.f2.pack()
            
        def press(self,value):
            """Set the value z"""
            if self['command']:
                self['command'](value)
            else:
                print 'You pressed z=',value

except ImportError:
    pass

if __name__ == "__main__":
    root=Tk()
    vt = PeriodicTable(root)
    vt.pack()
    root.mainloop()
