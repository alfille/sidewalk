#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  sidewalk.py
#  
#  Copyright 2018 Paul Alfille <paul.alfille@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

""" how many drops to cover a sidewalk
drops can be different sizes
output is either statistics or histogram
"""

class Globals:
    """ Global parameters """
    quiet = 0 # Quiet state
    scaled = 0
    CSV = None


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class Sidewalk:
    """Models a sidewalk aas a MxM grid with BitArray
    Note that for efficiency, the grid is alternatively set to 0 or 1
    The filling algorithm is varied based on dot size and binning
    """
    def __init__( self, mesh, dot ):
        self.mesh_side = mesh
        self.mesh_size = mesh*mesh
        self.dot_side = dot
        self.dot_size = dot*dot
        self.safe_side = self.mesh_side - self.dot_side
        self.sidewalk = BitArray( length=self.mesh_size )
        self.current =  False
        self.nex = True
        self.Header()
    
    def SingleDot( self ):
        self.sidewalk[random.randrange(self.mesh_size)] = self.nex

    def MultiDot( self ):
        iy = random.randrange(self.mesh_side)
        ix = random.randrange(self.mesh_side)
        for jy in range(self.dot_side):
            ky = ((iy+jy) % self.mesh_side)*self.mesh_side
            if ix <= self.safe_side:
                self.sidewalk.set( self.nex, range( ix+ky, ix+ky+self.dot_side ) )
            else:
                # split range
                for jx in range(self.dot_side):
                    self.sidewalk[ ky + (iy+jy)%self.mesh_side] = self.nex
    
    def Cover( self ):
        """One pass covering sidewalk, return number needed"""
        cover_count = 0
        
        if self.dot_side == 1:
            #simpler single dot
            while True:
                left = self.mesh_size - self.sidewalk.count(self.nex)
                if left == 0:
                    break ;
                cover_count += left
                for i in range(left):
                    self.SingleDot()
        else:
            while True:
                left = self.mesh_size - self.sidewalk.count(self.nex)
                if left == 0:
                    break ;
                for i in range(0,left,self.dot_size):
                    cover_count += 1
                    self.MultiDot()
        self.current = self.nex
        self.nex = not self.nex
        return cover_count
        
    def Coverbin( self, binwidth ):
        """One pass covering sidewalk, return bins needed"""
        bin_number = 0
        
        if self.dot_side == 1:
            #simpler single dot
            while True:
                if self.sidewalk.count(self.current) == 0 :
                    break ;
                bin_number += 1
                for i in range(binwidth):
                    self.SingleDot()
        else:
            while True:
                if self.sidewalk.count(self.current) == 0 :
                    break ;
                for i in range(binwidth):
                    bin_number += 1
                    self.MultiDot()
        self.current = self.nex
        self.nex = not self.nex
        return bin_number
        
    def Header(self):
        if Globals.quiet<2:
            print( "Sidewalk coverage\n\tMesh {:d} X {:d} = {:d}\n\tDot {:d} X {:d} = {:d}\n".format(self.mesh_side,self.mesh_side,self.mesh_size,self.dot_side,self.dot_side,self.dot_size))
        
class Data:
    """ Run Sidewalk for a given amount of times
    report header, data and stats
    """
    def __init__( self, mesh, dot, num ):
        sw = Sidewalk( mesh, dot )
        val = []
        for i in range( num ):
            v = sw.Cover()
            if Globals.quiet < 1:
                print(v)
            val.append(v)
        avg = sum(val) / num
        std = ( sum( (i-avg)**2 for i in val ) / (num-1) ) **.5
        print( "Average = {:f} STD = {:f} Num = {:d}\n".format(avg,std,num))
        if Globals.scaled:
            scale = mesh*mesh/(dot*dot)
            print( "Scaled:\n\tAverage = {:f} STD = {:f} Scale factor = {:f}\n".format(avg/scale,std/scale,scale))
        
class Bins:
    """ Run Sidewalk To fill bins
    """
    def __init__( self, mesh, dot, num, binwidth ):
        sw = Sidewalk( mesh, dot )
        val = {}
        for i in range( num ):
            v = sw.Coverbin(binwidth)
            if Globals.quiet < 1:
                print(v)
            if v in val:
                val[v] += 1
            else:
                val[v] = 1
        for i in range(max(val.keys())+1):
            if i not in val:
                val[i] = 0
            if Globals.scaled:
                print("\t{:d}, {:f}".format(i,val[i]/num) )
            else :
                print("\t{:d}, {:d}".format(i,val[i]) )
            if Globals.CSV:
                if Globals.scaled:
                    Globals.CSV.write("{:d},{:f}\n".format(i,val[i]/num) )
                else :
                    Globals.CSV.write("{:d},{:d}\n".format(i,val[i]) )

def CommandLine():
    """Setup argparser object to process the command line"""
    cl = argparse.ArgumentParser(description="Cover a sidewalk with drops. 2018 by Paul H Alfille")
    cl.add_argument("M",help="Number mash squares on side",type=int,nargs='?',default=100)
    cl.add_argument("D",help="Dot side",type=int,nargs='?',default=1)
    cl.add_argument("N",help="Number of passes",type=int,nargs='?',default=100)
    cl.add_argument("-b","--binwidth",help="Bin size for histogram",type=int,nargs='?',default=None)
    cl.add_argument("-c","--CSV",help="comma separated file",nargs='?', type=argparse.FileType('w'))
    cl.add_argument("-q","--quiet",help="Suppress more and more displayed info (can be repeated)",action="count")
    cl.add_argument("-s","--scaled",help="Show data scaled",action="store_true")
    return cl.parse_args()

def main(args):
    args = CommandLine() # Get args from command line

    if args.quiet:
        Globals.quiet = args.quiet
    if args.scaled:
        Globals.scaled = args.scaled
    if args.CSV:
        Globals.CSV = args.CSV
    if args.binwidth != None:
        if args.binwidth < 1:
            print("Binwidth = {:d}".format(args.M*args.M))
            Bins( args.M, args.D, args.N, args.M*args.M )
        else:
            Bins( args.M, args.D, args.N, args.binwidth )
            
        #print("bin={:d}".format(args.binwidth))
    else:
        Data( args.M, args.D, args.N )
    
    return 0

if __name__ == '__main__':
    import sys
    import argparse # for parsing the command line
#    import BitArray
#    import bitarray
    from bitstring import BitArray
    import random
    #import matplotlib.pyplot as plt
    
    sys.exit(main(sys.argv))
