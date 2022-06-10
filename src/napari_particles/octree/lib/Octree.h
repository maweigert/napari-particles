#ifndef Octree_H
#define Octree_H

#include <cstddef>
#include <vector>
#include <iostream>
#include "OctreePoint.h"

class Octree {
    public: 

    // Physical position/size. This implicitly defines the bounding 
    // box of this node
    Vec3 origin;         //! The physical center of this node
    Vec3 halfDimension;  //! Half the width/height/depth of this node

    // The tree has up to eight children and can additionally store
    // a point, though in many applications only, the leaves will store data.
    Octree *children[8]; //! Pointers to child octants
    int id;   //! the id of the node
    Vec3 position;
    /*
            Children follow a predictable pattern to make accesses simple.
            Here, - means less than 'origin' in that dimension, + means greater than.
            child:	0 1 2 3 4 5 6 7
            x:      - - - - + + + +
            y:      - - + + - - + +
            z:      - + - + - + - +
        */

    public:
    Octree(const Vec3& origin, const Vec3& halfDimension) 
        : origin(origin), halfDimension(halfDimension), id(-1), position(Vec3(0,0,0)) {
            // Initially, there are no children
            for(int i=0; i<8; ++i) 
                children[i] = NULL;
        }

    Octree(const Octree& copy)
        : origin(copy.origin), halfDimension(copy.halfDimension), id(copy.id), position(copy.position) {

        }

    ~Octree() {
        // Recursively destroy octants
        for(int i=0; i<8; ++i) 
            delete children[i];
    }

    // Determine which octant of the tree would contain 'point'
    int getOctantContainingPoint(const Vec3& point) const {
        int oct = 0;
        if(point.x >= origin.x) oct |= 4;
        if(point.y >= origin.y) oct |= 2;
        if(point.z >= origin.z) oct |= 1;
        return oct;
    }

    bool isLeafNode() const {
        // This is correct, but overkill. See below.
        /*
                for(int i=0; i<8; ++i)
                if(children[i] != NULL) 
                return false;
                return true;
            */

        // We are a leaf iff we have no children. Since we either have none, or 
        // all eight, it is sufficient to just check the first.
        return children[0] == NULL;
    }

    void insert(const int id, Vec3& point) {
        // If this node doesn't have a data point yet assigned 
        // and it is a leaf, then we're done!
        
        if(isLeafNode()) {
            if(this->id==-1) {
                this->id = id;
                this->position = point;
                return;
            } else {


                // We're at a leaf, but there's already something here
                // We will split this node so that it has 8 child octants
                // and then insert the old data that was here, along with 
                // this new data point

                // Save this data point that was here for a later re-insert
                int  oldID = this->id;
                Vec3 oldPoint = this->position;
                this->id = -1;

                // Split the current node and create new empty trees for each
                // child octant.
                for(int i=0; i<8; ++i) {
                    // Compute new bounding box for this child
                    Vec3 newOrigin = origin;
                    newOrigin.x += halfDimension.x * (i&4 ? .5f : -.5f);
                    newOrigin.y += halfDimension.y * (i&2 ? .5f : -.5f);
                    newOrigin.z += halfDimension.z * (i&1 ? .5f : -.5f);
                    children[i] = new Octree(newOrigin, halfDimension*.5f);
                }

                // Re-insert the old point, and insert this new point
                // (We wouldn't need to insert from the root, because we already
                // know it's guaranteed to be in this section of the tree)
                children[getOctantContainingPoint(oldPoint)]->insert(oldID, oldPoint);
                children[getOctantContainingPoint(point)]->insert(id, point);
            }
        } else {
            // We are at an interior node. Insert recursively into the 
            // appropriate child octant
            int octant = getOctantContainingPoint(point);
            children[octant]->insert(id, point);
        }
    }

};

#endif
