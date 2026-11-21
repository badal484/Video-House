# CHARACTER RIGGING & 2D SKELETAL SYSTEM SPECIFICATION
**Department:** 10_animation_2d  
**Topic:** Hierarchical Bone Nodes, Forward & Inverse Kinematics, Cut-Out Puppets, and Facial Visemes  

---

## 1. 2D Bone Node Hierarchy

A 2D character rig is structured as a directed tree of bone nodes originating from the root pelvis:

```
[ Root / Pelvis ]
   ├──► [ Spine ]
   │       └──► [ Chest ]
   │               ├──► [ Neck ] ──► [ Head ]
   │               ├──► [ Left Shoulder ] ──► [ Left Upper Arm ] ──► [ Left Forearm ] ──► [ Left Hand ]
   │               └──► [ Right Shoulder ] ──► [ Right Upper Arm ] ──► [ Right Forearm ] ──► [ Right Hand ]
   ├──► [ Left Hip ] ──► [ Left Thigh ] ──► [ Left Shin ] ──► [ Left Foot ]
   └──► [ Right Hip ] ──► [ Right Thigh ] ──► [ Right Shin ] ──► [ Right Foot ]
```

Each bone contains:
- `bone_id`: Unique identifier (e.g. `upper_arm_l`).
- `parent_id`: Parent bone ID (or `None` for root).
- `length`: Physical length in pixels.
- `local_position`: $(x, y)$ relative to parent bone tip.
- `local_rotation`: Angle in radians relative to parent orientation.
- `local_scale`: $(s_x, s_y)$ scale factors.

---

## 2. Forward & Inverse Kinematics

### 2.1 Forward Kinematics (FK)
World-space positions are evaluated recursively down the hierarchy:
$$M_{world, i} = M_{world, parent} \times M_{local, i}$$
Where $M$ is the $3 \times 3$ affine transformation matrix.

### 2.2 Analytical 2-Bone Inverse Kinematics (IK)
For limbs (thigh + shin to foot target, or upper arm + forearm to hand target), given upper bone length $l_1$, lower bone length $l_2$, root position $P_0$, and target position $P_{target}$:

1. Distance to target:
   $$d = \|P_{target} - P_0\|$$
   Clamped to maximum reach: $d_{clamped} = \min(d, (l_1 + l_2) \times 0.9999)$.

2. Law of Cosines for elbow/knee angle $\theta_2$:
   $$\cos(\alpha_2) = \frac{l_1^2 + l_2^2 - d_{clamped}^2}{2 l_1 l_2}$$
   $$\theta_2 = \pi - \alpha_2$$

3. Base angle to target $\theta_{target} = \text{atan2}(P_{y, target} - P_{y, 0}, P_{x, target} - P_{x, 0})$ and offset angle $\alpha_1$:
   $$\cos(\alpha_1) = \frac{l_1^2 + d_{clamped}^2 - l_2^2}{2 l_1 d_{clamped}}$$
   $$\theta_1 = \theta_{target} \pm \alpha_1$$ (sign determined by clockwise/counter-clockwise bend preference).

---

## 3. Cut-Out Puppet Layering & Pivots

In 2D cut-out animation, character body parts are illustrated as independent graphical sprites. Each sprite specifies an explicit **pivot point** $(px, py)$ relative to its bounding box:
- Upper Arm: Pivot at shoulder joint socket.
- Forearm: Pivot at elbow joint socket.
- Hand: Pivot at wrist joint.
- Head: Pivot at base of neck.

Sprites are mapped directly to corresponding bone transforms and drawn in strict Z-depth order (e.g. Back Arm $\to$ Torso $\to$ Head $\to$ Front Arm) to prevent self-intersection visual bugs.
