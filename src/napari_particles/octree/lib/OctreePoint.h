#ifndef OctreePoint_H
#define OctreePoint_H

#include "Vec3.h"

class OctreePoint {
	Vec3 position; 
public:
	OctreePoint() { }
	OctreePoint(const Vec3& position) : position(position) { }
	inline const Vec3& getPosition() const { return position; }
	inline void setPosition(const Vec3& p) { position = p; }
};

#endif
