#!/usr/bin/env python3

import random

spp_dict = { 'E.coli':
                         { 'growth_rate' : 3,
                           'kin_select'  : random.randrange(0,10),
                           'defenses'    : ''},
             'M.tuberculosis':
                         { 'growth_rate' : 1,
                           'kin_select'  : random.randrange(0,3),
                           'defenses'    : ''},
             'V.parramaris':
                         { 'growth_rate' : 0.5,
                           'kin_select'  : random.randrange(0,4),
                           'defenses'    : ''},
             'M.alcalica':
                         { 'growth_rate' : 2,
                           'kin_select'  : random.randrange(0,4),
                           'defenses'    : ''},
             'S.aureus':
                         { 'growth_rate' : 2.5,
                           'kin_select'  : random.randrange(0,5),
                           'defenses'    : ''},
             'V.neptunis':
                         { 'growth_rate' : 2,
                           'kin_select'  : random.randrange(0,1),
                           'defenses'    : ''},
             'P.fluorescens':
                         { 'growth_rate' : 2,
                           'kin_select'  : random.randrange(0,6),
                           'defenses'    : ''},
             'K.pneumoniae':
                         { 'growth_rate' : 2.8,
                           'kin_select'  : random.randrange(0,8),
                           'defenses'    : ''}
}          

print(spp_dict['E.coli']['kin_select'])                         
