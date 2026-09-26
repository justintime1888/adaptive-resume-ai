# 📄 Master Resume & Experience Bank

> Use this file as your single source of truth for all technical skills, projects, work experience, and coursework. The AI Resume Tailorer ([`tailor_resume.py`](file:///C:/Users/jstnp/Documents/obsidianvault/scripts/tailor_resume.py)) pulls from this bank to generate custom ATS-optimized resumes for specific job descriptions.
>
> 📁 **LaTeX Source File:** [`Justin_Parra_Master_Resume_Everything.tex`](file:///C:/Users/jstnp/Documents/obsidianvault/04-Career/LaTeX/Justin_Parra_Master_Resume_Everything.tex)  
> 📄 **Compiled Master PDF:** [`Justin_Parra_Master_Resume_Everything.pdf`](file:///C:/Users/jstnp/Documents/obsidianvault/04-Career/LaTeX/Justin_Parra_Master_Resume_Everything.pdf)

---

## 👤 Personal Information
- **Name:** Justin M. Parra
- **Location:** Dunellen, NJ
- **Phone:** (732) 772-5709
- **Email:** `jstnp18@gmail.com` | `jmp715@scarletmail.rutgers.edu`
- **LinkedIn:** [linkedin.com/in/justin-parra-/](https://www.linkedin.com/in/justin-parra-/)
- **GitHub:** [github.com/justintime1888](https://github.com/justintime1888)
- **Portfolio:** [justinparra.dev](https://justin-parra-vercel.vercel.app/)

---

## 🎯 Engineering Profile & Core Focus
Electrical and Computer Engineering student at **Rutgers University – New Brunswick** (graduating May 2027) specializing in embedded firmware architecture, real-time control algorithms, mixed-signal hardware design, and autonomous robotics.
- **Core Specializations:** Bare-Metal & RTOS Firmware Architecture, Cascade PID Control, Sensor Fusion (EMA / EKF Principles), A* & Modified Flood Fill Pathfinding, 4-Layer PCB Design (Altium Designer / KiCad), and POSIX Telemetry Simulation.
- **Target Engineering Domains:** Embedded Software Engineering, Firmware Engineering, Robotics & Controls, Microcontroller Architectures, Semiconductor/EDA Tooling, and Hardware / Digital Systems Design.

---

## 🎓 Education & Coursework
- **University:** Rutgers University – New Brunswick, NJ
- **Degree:** Bachelor of Science in Electrical and Computer Engineering (ECE)
- **Expected Graduation:** May 2027
- **Coursework:**
  - **Circuits & Microelectronics:** Principles of Electrical Engineering I & II (AC/DC Circuits, Transients, Phasors, Impedance, Op-Amps, Frequency Response, Resonance), Microelectronic Circuits
  - **Systems, Signals & Controls:** Linear Systems and Signals, Control Systems Principles, Feedback & State Estimation, Sensor Fusion
  - **Computer Engineering & Architectures:** Digital Logic Design, Computer Architecture, Embedded Systems & Microcontrollers, Programming Methodology I & II (Modern C/C++, Data Structures & Algorithms)
  - **Mathematics & Physics:** Differential Equations for Engineering & Physics (MATH 244), Multivariable Calculus, Linear Algebra, Discrete Mathematics
  - **Energy & Capstone:** Sustainable Energy Systems (14:332:402), Introduction to ECE Capstone Design

---

## 💼 Engineering Work Experience

### 🐭 Rutgers Micromouse — Co-President & Lead Hardware/Firmware Engineer
*September 2024 – Present | New Brunswick, NJ*
- Developed embedded firmware in C/C++ on STM32F405 and ESP32-S3 microcontrollers for real-time motion control and sensor fusion utilizing FreeRTOS.
- Designed and routed custom 4-layer PCBs in KiCad and Altium Designer with ENIG surface finish, integrating STM32F405, IMU, optical ToF sensors, and dual H-bridge motor drivers.
- Led a 40+ member engineering organization as Co-President, secured $2,500+ in corporate sponsorship to fund custom PCB fabrication, and guided the team to 2nd Place at the 2025 Rowan Regional Competition.
- Implemented real-time Flood-Fill maze navigation and cascaded PID motion control loops in modern C++ to stabilize heading and velocity errors during autonomous traversal.
- Characterized signal integrity, bus rise times, and multi-slave arbitration across 400 kHz I²C and SPI lines using mixed-signal oscilloscopes and logic analyzers.

### 🏭 LPT-KEYPAK — Engineering Intern
*June 2024 – August 2024 | Tewksbury, NJ*
- Commissioned and validated automated high-speed packaging machinery for the Bill & Melinda Gates Foundation, increasing packaging line throughput by 30%.
- Diagnosed electromechanical failure points in automated manufacturing equipment, reducing production defect rates by 15%.
- Interpreted 20+ complex industrial electrical schematics to troubleshoot PLCs, motor drives, and sensor relays, establishing standardized maintenance SOPs.
- Validated sensor calibration, voltage tolerances, and relay timing margins using digital storage oscilloscopes and precision multimeters.

### 🤖 VEX Robotics (Rutgers IEEE) — Lead Electrical Engineer
*September 2024 – Present | New Brunswick, NJ*
- Designed communication and power distribution architecture using the VEX Brain, enabling RS-485 to UART to I2C data transfer between embedded subsystems.
- Selected and integrated differential transceivers, TVS surge protection diodes, decoupling capacitors, and pull-up/down resistors to protect logic from inductive spikes and signal reflections.
- Conducted functional bench testing and signal integrity validation on serial communication lines using digital oscilloscopes to ensure reliable data transmission across competition runs.
- Managed wiring harness fabrication, power budgeting across multi-motor drive subsystems, and electrical subsystem compliance under strict competition rules.

---

## 🚀 Engineering & Technical Projects Portfolio

### 🏆 1. Autonomous Micromouse Robot ("Jerrieee") — 2nd Place (Rowan Regionals)
*C/C++, STM32F405RG, KiCad 8.0, 4-Layer ENIG PCB, DRV8847, VL6180X ToF, Cascaded PID* | [GitHub Repo](https://github.com/justintime1888/Micromouse-2025)
- Won 2nd Place at Rowan Regional Competition; designed custom 4-layer ENIG PCB integrating 168 MHz ARM Cortex-M4 MCU, 5x optical ToF array over 400 kHz I²C, and dual DRV8847 motor drivers in an 84x76.5 mm chassis.
- Programmed real-time Flood-Fill maze navigation algorithm running in <850 µs per cell transition with a 1 kHz cascaded PID control loop correcting gyro heading and velocity errors up to 4.2 m/s with zero integral windup.

### ⚡ 2. 4-Way Traffic Signal Controller
*555 Timers, Digital Logic, Combinational Circuits, State Machine Timing, Oscilloscope*
- Engineered a discrete hardware finite state controller using 555 timer astable clock generators, binary counters, and logic gates to sequence multi-phase traffic signal intervals.
- Verified state transitions, propagation delays, and switching noise using benchtop oscilloscopes and digital multimeters, ensuring zero spurious transition states.

### ⚡ 3. Analog Filter & Transient Signal Conditioning Analyzer
*LTspice, MATLAB, Signal Integrity, Active Op-Amp Filters, Transient Analysis*
- Simulated active 2nd-order RLC filter topologies and operational amplifier stages in LTspice, evaluating AC frequency responses, Bode phase margins, and transient damping factors.
- Designed hardware low-pass signal conditioning stages to suppress inductive switching transients from high-current DC motors, preventing ADC input distortion and verifying performance with benchtop instrumentation.

### 📷 4. Autonomous Vision Line-Following Robot
*Embedded C++, ESP32-S3, OV2640 Camera, FreeRTOS, PlatformIO, Closed-Loop PID Control*
- Built an autonomous mobile robot using an ESP32-S3 microcontroller and OV2640 camera module, developing an onboard vision-processing pipeline in C++ to detect track curvature in real time.
- Tuned closed-loop PID control algorithms for dual DC motors, maintaining trajectory tracking stability at speeds up to 1.2 m/s with zero track departures.

### 📊 5. POSIX Robotics Simulation & Telemetry Engine
*C++, Qt6, Python, NumPy, SciPy, Matplotlib, PySerial, POSIX Pipes, Arch Linux*
- Built a headless simulation pipeline in Qt6/C++ benchmarking pathfinding algorithms across 100+ competition maze layouts over POSIX inter-process pipes under Arch Linux.
- Developed a real-time serial telemetry data logger and visualizer capturing motor PWM output, angular error, and ToF distance streams at 100 Hz using Python and Matplotlib to benchmark PID settling time and overshoot.

### ⚡ 6. Analog Filter & Transient Signal Conditioning Analyzer
*LTspice, MATLAB, Signal Integrity, Circuit Modeling, AC Frequency Response, PEE II*
- Simulated active 2nd-order RLC filter topologies and operational amplifier stages in LTspice, evaluating AC frequency responses, Bode phase margins, and transient damping factors.
- Designed hardware low-pass signal conditioning stages to suppress inductive switching transients from high-current DC motors, preventing ADC input distortion and verifying performance with benchtop instrumentation.

### 🚦 7. Pedestrian Traffic Control System (Hardware State Controller)
*Discrete Logic, 555 Timers, Decade Counters, Combinational Logic Gates, Circuit Timing Analysis, Multisim*
- Designed and breadboarded a four-way traffic controller using 555 timers, decade counters, and combinational logic gates to simulate asynchronous pedestrian crossing requests.
- Analyzed clock propagation delays, race conditions, and switching thresholds with bench oscilloscopes to ensure fail-safe state transitions; authored full engineering design report.

### 📈 8. Experimental Telemetry & Statistical Data Analysis Pipeline
*Python, NumPy, SciPy, Matplotlib, Data Analysis & Visualization*
- Built an automated statistical analysis pipeline in Python processing 100+ experimental test runs to evaluate transient settling metrics, overshoot variance, and parameter confidence intervals.
- Generated visual dashboards and distribution plots for experimental data interpretation, identifying process outliers and driving closed-loop system tuning.

---

## 🛠️ Comprehensive Technical Skills

| Category | Technologies, Platforms & Tools |
| :--- | :--- |
| **Programming Languages** | C, C++ (C++11/17/20), Python (NumPy, SciPy, Matplotlib, PySerial), TypeScript/JavaScript, MATLAB, Java, Verilog HDL, Assembly (x86/ARM), Bash/Shell, SQL, Spanish (Native/Bilingual) |
| **Embedded & Microcontrollers** | ESP32-S3 (Dual-Core Xtensa 32-bit), STM32F405 / STM32 (ARM Cortex-M4), Arduino, FreeRTOS Multitasking, Bare-Metal C, HAL, Direct Register I/O, Timer ISRs, DMA, Bootloaders |
| **Hardware & Circuit Design** | Altium Designer, KiCad 8.0 (4-Layer PCB Routing, ENIG Finish, Controlled Impedance, Coplanar Ground Shielding), EasyEDA, Digital Logic Design, Analog Signal Conditioning, Active Op-Amp Filters, RLC Transient Analysis, TVS Surge Protection, Decoupling |
| **Protocols & Communication** | I²C (Standard & 400 kHz Fast-Mode), SPI, UART, RS-485 Differential Bus, CAN Bus, PWM Motor Control, GPIO, ADC/DAC |
| **Robotics & Controls** | Dual-Loop Cascade PID Control, Discrete Velocity Control, Sensor Fusion (EMA, Complementary, EKF Principles), Differential Drive Kinematics, State Estimation, Modified Flood Fill, A* Pathfinding, Raycast Modeling |
| **EDA, Simulation & CAD** | Altium Designer, KiCad 8.0, LTspice, Multisim, SOLIDWORKS (3D CAD), Qt6 Framework (MMS Simulator), ElkJS Graph Routing, 3D Printing (FDM/SLA) |
| **Lab Equipment & Testing** | Mixed-Signal & Digital Storage Oscilloscopes (DSO), Logic Analyzers, Benchtop Power Supplies, Function Generators, Digital Multimeters (DMM), Soldering & SMD Rework |
| **Developer Environments** | Linux (Arch Linux, Ubuntu, WSL2), Git / GitHub, CMake, Make, GDB Debugger, PlatformIO, VS Code, POSIX Inter-Process Communication (IPC) |

---

## 🌟 Leadership & Affiliations
- **Rutgers Micromouse (IEEE Student Branch):** Co-President & Team Lead (September 2024 – Present) — Directed technical onboarding workshops on embedded C++, PCB layout in Altium Designer/KiCad, and cascade PID control for 40+ engineering undergraduates; managed team operations and secured $2,500+ in industry funding.
- **Rowan Regional Micromouse Competition:** **2nd Place Regional Finalist** (2025) — Designed chassis, 4-layer PCB, and firmware for the autonomous maze robot "Jerrieee".
- **IEEE Rutgers Student Chapter:** Active Member & Project Lead (September 2023 – Present) — Competed in collegiate robotics design challenges, autonomous hardware hackathons, and regional IEEE technical symposiums.
