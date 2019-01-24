#!/usr/bin/env python3
"""
Example of how bodies interact with each other. For a body to be able to
move it needs to have joints. In this example, the "robot" is a red ball
with X and Y slide joints (and a Z slide joint that isn't controlled).
On the floor, there's a cylinder with X and Y slide joints, so it can
be pushed around with the robot. There's also a box without joints. Since
the box doesn't have joints, it's fixed and can't be pushed around.
"""
from mujoco_py import load_model_from_xml, MjSim, MjViewer
import math
import numpy as np
import os

# world constants
dt = 0.001
gravity = 9.81

MODEL_XML = """
<mujoco model="quadrotor0">
	<compiler inertiafromgeom="true" coordinate="local"/>
	<option	timestep="{timestep}" gravity="0 0 -{gravity}" density="1" viscosity="1e-5" />
	<worldbody>
		<geom name="floor" pos="0 0 0" size="2 2 .2" type="plane"  conaffinity="1" rgba="1 1 1 1" condim="3"/>
		<body name="quadrotor" pos="0 0 0" >
			<geom name="core" type="box" pos="0 0 0" quat = "1. 0. 0. 0" size="0.06 0.035 0.025"  rgba="0.3 0.3 0.8 1" mass = ".1"/>
			
			<geom name="a00" type="box" pos=".071 0.071 0.0" size="0.05 0.01 0.0025"  quat = ".924 0.0 0.0 0.383" rgba="0.3 0.3 0.8 1" mass = ".025"/>
			<geom name="a10" type="box" pos=".071 -0.071 0.0" size="0.05 0.01 0.0025"  quat = ".383 0.0 0.0 0.924" rgba="0.3 0.3 0.8 1" mass = ".025"/>
			<geom name="a20" type="box" pos="-0.071 -0.071 0.0" size="0.05 0.01 0.0025"  quat = "-.383 0.0 0.0 0.924" rgba="0.3 0.3 0.8 1" mass = ".025"/>
			<geom name="a30" type="box" pos="-.071 0.071 0.0" size="0.05 0.01 0.0025"  quat = ".924 0.0 0.0 -0.383" rgba="0.3 0.3 0.8 1" mass = ".025"/>
			
			<joint name="root"   type="free" damping="0" armature="0" pos="0 0 0" />
			
			<!-- Motor sites to attach motor actuators --->
            <site name="motor0" type="cylinder" pos=" 0.1  0.1 0.01"  size="0.01 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1"/>
            <site name="motor1" type="cylinder" pos=" 0.1 -0.1 0.01"  size="0.01 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1"/>
            <site name="motor2" type="cylinder" pos="-0.1 -0.1 0.01"  size="0.01 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1"/>
            <site name="motor3" type="cylinder" pos="-0.1  0.1 0.01"  size="0.01 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1"/>
			
			<!-- Thruster geometries for collisions since site's are excluded from collision checking --->
            <geom name="thruster0" type="cylinder" pos=" 0.1  0.1  0.01" size="0.05 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1" mass = ".025"/>
            <geom name="thruster1" type="cylinder" pos=" 0.1 -0.1  0.01" size="0.05 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1" mass = ".025"/>
            <geom name="thruster2" type="cylinder" pos="-0.1 -0.1  0.01" size="0.05 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1" mass = ".025"/>
            <geom name="thruster3" type="cylinder" pos="-0.1  0.1  0.01" size="0.05 0.0025"  quat = "1.0 0.0 0.0 0." rgba="0.3 0.8 0.3 1" mass = ".025"/>
            
            <!-- Visualization of the coordinate frame --->
			<site name="qcX" type="box" pos="0.1 0.0 0.0" size="0.1 0.005 0.005"  quat = " 1.000  0.0  0.0    0."     rgba="1 0 0 1" />
			<site name="qcY" type="box" pos="0.0 0.1 0.0" size="0.1 0.005 0.005"  quat = " 0.707  0.0  0.0    0.707"  rgba="0 1 0 1" />
			<site name="qcZ" type="box" pos="0.0 0.0 0.1" size="0.1 0.005 0.005"  quat = "-0.707  0.0  0.707  0."     rgba="0 0 1 1" />
		</body>
	</worldbody>
    <actuator>
        <motor ctrllimited="true" ctrlrange="0.0 10.0" gear="1  0. 00. 0. 0. 0." site="motor0"/>
        <motor ctrllimited="true" ctrlrange="0.0 10.0" gear="1  0. 00. 0. 0. 0." site="motor1"/>
        <motor ctrllimited="true" ctrlrange="0.0 10.0" gear="1  0. 00. 0. 0. 0." site="motor2"/>
        <motor ctrllimited="true" ctrlrange="0.0 10.0" gear="1  0. 00. 0. 0. 0." site="motor3"/>
	</actuator>
</mujoco>
""".format(timestep=dt, gravity=gravity)

model = load_model_from_xml(MODEL_XML)
sim = MjSim(model)
viewer = MjViewer(sim)

t = 0
e = 0

# constant
mass = 0.3

# desire state (z, r, p, y)
x_d = np.array([
    0.5,
    0.0,
    0.0,
    0.0,
])

# control matrix
kpz = 4.
kpphi = 0.01
kptheta = 0.01
kppsi = 0.01

K_p = np.array([
    [kpz, 0, 0, 0],
    [0, kpphi, 0, 0],
    [0, 0, kptheta, 0],
    [0, 0, 0, kppsi],
])

kdz = 0.01
kdphi = 0.01
kdtheta = 0.01
kdpsi = 0.01

K_d = np.array([
    [kdz, 0, 0, 0],
    [0, kdphi, 0, 0],
    [0, 0, kdtheta, 0],
    [0, 0, 0, kdpsi],
])

# moment arm (L_arm cos 45) 
L = 0.1

# constant factor
C = 0.1

# rotor matrix
a = 0.25
b = 1 / (4*L)
c = 1 / (4*C)

C_R = np.array([
    [a, b, -b, -c],
    [a, -b, -b, c],
    [a, -b, b, -c],
    [a, b, b, c],
])

# loop
while True:

    # rpy
    rotmat = sim.data.get_body_xmat('quadrotor')

    yaw = np.arctan2(rotmat[1][0], rotmat[0][0])
    pitch = np.arctan2(-rotmat[2][0], np.sqrt(rotmat[2][1]**2 + rotmat[2][2]**2))
    roll = np.arctan2(rotmat[2][1], rotmat[2][2])

    # state
    x = np.array([
        sim.data.get_body_xipos('quadrotor')[2],
        roll,
        pitch,
        yaw,
    ])

    # error
    e_last = e
    e = x_d - x
    e_dot = (e - e_last)/dt

    print(e)

    # input
    u = np.matmul(K_p, e) + np.matmul(K_d, e_dot)
    u += np.array([u[0] + mass * gravity, 0, 0, 0]) 

    # actuator input 
    F = np.matmul(C_R, u)

    sim.data.ctrl[0] = F[0]     # +,+
    sim.data.ctrl[1] = F[1]     # +,-
    sim.data.ctrl[2] = F[2]     # -,-
    sim.data.ctrl[3] = F[3]     # -,+

    t += 1
    sim.step()
    viewer.render()
    if t > 100 and os.getenv('TESTING') is not None:
        break