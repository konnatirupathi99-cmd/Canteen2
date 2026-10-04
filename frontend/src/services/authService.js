const mockUsers = [
  { id: 1, role: 'MANAGER', email: 'manager@example.com', mobile: '+919999999999', password: 'Password123!', name: 'System Admin' },
  { id: 2, role: 'STUDENT', collegeEmail: 'student@college.edu', mobile: '+918888888888', password: 'Password123!', name: 'John Doe' },
  { id: 3, role: 'FACULTY', collegeEmail: 'faculty@college.edu', facultyId: 'FAC-1024', mobile: '+917777777777', password: 'Password123!', name: 'Dr. Smith' }
];

const delay = (ms) => new Promise(res => setTimeout(res, ms));

export const authService = {
  async login(credentials) {
    await delay(1500); // Simulate network latency
    const { role, email, mobile, password, facultyId } = credentials;
    
    let user;
    if (role === 'MANAGER') {
      user = mockUsers.find(u => u.role === 'MANAGER' && u.email === email && u.mobile === mobile && u.password === password);
    } else if (role === 'STUDENT') {
      user = mockUsers.find(u => u.role === 'STUDENT' && u.collegeEmail === email && u.mobile === mobile && u.password === password);
    } else if (role === 'FACULTY') {
      user = mockUsers.find(u => 
        u.role === 'FACULTY' && 
        u.mobile === mobile && 
        u.password === password && 
        (u.collegeEmail === email || u.facultyId === facultyId)
      );
    }

    if (user) {
      // Create secure mock session
      const token = btoa(JSON.stringify({ id: user.id, role: user.role, name: user.name }));
      localStorage.setItem('canteen_token', token);
      return { success: true, user: { id: user.id, role: user.role, name: user.name } };
    } else {
      throw new Error("Unable to authenticate with the provided credentials.");
    }
  },

  async register(data) {
    await delay(2000);
    const { role, password } = data;
    
    // Basic mock duplicate check
    let exists = false;
    if (role === 'STUDENT') {
      exists = mockUsers.some(u => u.role === 'STUDENT' && (u.collegeEmail === data.collegeEmail || u.studentId === data.studentId));
    } else if (role === 'FACULTY') {
      exists = mockUsers.some(u => u.role === 'FACULTY' && (u.collegeEmail === data.collegeEmail || u.facultyId === data.facultyId));
    } else if (role === 'MANAGER') {
      exists = mockUsers.some(u => u.role === 'MANAGER' && u.email === data.personalEmail);
    }
    
    if (exists) {
      throw new Error("An account using these credentials already exists.");
    }

    const newUser = {
      id: Date.now(),
      role,
      password,
      name: data.fullName,
      mobile: data.mobile
    };

    if (role === 'STUDENT') {
      newUser.collegeEmail = data.collegeEmail;
      newUser.studentId = data.studentId;
    } else if (role === 'FACULTY') {
      newUser.collegeEmail = data.collegeEmail;
      newUser.facultyId = data.facultyId;
    } else if (role === 'MANAGER') {
      newUser.email = data.personalEmail;
    }

    mockUsers.push(newUser);

    return { 
      success: true, 
      message: role === 'MANAGER' ? "Your manager account has been created successfully." : `Your ${role.toLowerCase()} account has been created successfully.`
    };
  },

  logout() {
    localStorage.removeItem('canteen_token');
  },

  getCurrentUser() {
    try {
      const token = localStorage.getItem('canteen_token');
      if (token) return JSON.parse(atob(token));
      return null;
    } catch {
      return null;
    }
  }
};
