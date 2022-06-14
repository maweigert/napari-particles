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
    std::vector<int> idx;   //! the id of the node
    std::vector<Vec3> positions;
    const int max_items;
    /*
            Children follow a predictable pattern to make accesses simple.
            Here, - means less than 'origin' in that dimension, + means greater than.
            child:	0 1 2 3 4 5 6 7
            x:      - - - - + + + +
            y:      - - + + - - + +
            z:      - + - + - + - +
        */

    public:
    Octree(const Vec3& origin, const Vec3& halfDimension, const int max_items=1) 
        : origin(origin), halfDimension(halfDimension), max_items(max_items) {
            // Initially, there are no children
            for(int i=0; i<8; ++i) 
                children[i] = NULL;
        }

    Octree(const Octree& copy)
        : origin(copy.origin), halfDimension(copy.halfDimension), idx(copy.idx), positions(copy.positions), max_items(copy.max_items) {

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

    // Determine whether point is in current njode
    bool isInside(const Vec3& point) const {
        return ((point.x >= origin.x-halfDimension.x) && (point.x < origin.x+halfDimension.x) &&
        (point.y >= origin.y-halfDimension.y) && (point.y < origin.y+halfDimension.y) &&
        (point.z >= origin.z-halfDimension.z) && (point.z < origin.z+halfDimension.z));
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
            if(this->idx.size()<max_items) {
                this->idx.push_back(id);
                this->positions.push_back(point);
                return;
            } else {


                // We're at a leaf and we are full
                // We will split this node so that it has 8 child octants
                // and then insert the old data that was here, along with 
                // this new data point

                // Save this data point that was here for a later re-insert
                std::vector<int>  oldIDs = this->idx;
                std::vector<Vec3> oldPoints = this->positions;

                this->idx.clear();
                this->positions.clear();

                // Split the current node and create new empty trees for each
                // child octant.
                for(int i=0; i<8; ++i) {
                    // Compute new bounding box for this child
                    Vec3 newOrigin = origin;
                    newOrigin.x += halfDimension.x * (i&4 ? .5f : -.5f);
                    newOrigin.y += halfDimension.y * (i&2 ? .5f : -.5f);
                    newOrigin.z += halfDimension.z * (i&1 ? .5f : -.5f);
                    children[i] = new Octree(newOrigin, halfDimension*.5f, max_items);
                }

                // Re-insert the old point, and insert this new point
                // (We wouldn't need to insert from the root, because we already
                // know it's guaranteed to be in this section of the tree)
                for (size_t i = 0; i < oldIDs.size(); i++)
                {
                    children[getOctantContainingPoint(oldPoints[i])]->insert(oldIDs[i], oldPoints[i]);        
                }
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
