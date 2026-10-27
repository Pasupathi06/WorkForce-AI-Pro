import axios from "axios";

const host = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "127.0.0.1";
const DEFAULT_API_BASE_URL = `http://${host}:8000/api/v1`;

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");

const TOKEN_KEY = "workforce_access_token";
const USER_KEY = "workforce_current_user";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

function clearStoredSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function getErrorMessage(error) {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg || "Invalid input").join(", ");
    }

    return "The server returned an error.";
  }

  if (error?.code === "ECONNABORTED") {
    return "The request timed out. Please try again.";
  }

  if (!error?.response) {
    return "Unable to connect to the server. Please check your connection.";
  }

  return error?.message || "Something went wrong. Please try again.";
}

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);

    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const statusCode = error.response?.status;
    const requestUrl = error.config?.url || "";

    const isLoginRequest = /\/auth\/login\/?$/.test(requestUrl);
    const isRegistrationRequest = /\/auth\/register\/?$/.test(requestUrl);

    if (
      statusCode === 401 &&
      !isLoginRequest &&
      !isRegistrationRequest
    ) {
      clearStoredSession();
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (credentials) => {
    clearStoredSession();

    try {
      const response = await api.post("/auth/login", credentials);
      const data = response.data;

      if (!data?.access_token) {
        throw new Error("Login response did not contain an access token.");
      }

      localStorage.setItem(TOKEN_KEY, data.access_token);

      if (data.user && typeof data.user === "object") {
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      } else {
        localStorage.removeItem(USER_KEY);
      }

      return data;
    } catch (error) {
      clearStoredSession();
      throw error;
    }
  },

  register: async (userData) => {
    const response = await api.post("/auth/register", userData);
    return response.data;
  },

  me: async () => {
    const response = await api.get("/auth/me");
    const user = response.data;
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
  },

  listUsers: async () => {
    const response = await api.get("/auth/users");
    return response.data;
  },

  availableEmployeeUsers: async () => {
    const response = await api.get("/auth/users/available-for-employees");
    return response.data;
  },

  updateUserRole: async (userId, role) => {
    const response = await api.patch(`/auth/users/${userId}/role`, { role });
    return response.data;
  },

  logout: async () => {
    clearStoredSession();
    return { message: "Logged out successfully." };
  },

  getToken: () => localStorage.getItem(TOKEN_KEY),

  getStoredUser: () => {
    const user = localStorage.getItem(USER_KEY);

    if (!user) return null;

    try {
      return JSON.parse(user);
    } catch {
      localStorage.removeItem(USER_KEY);
      return null;
    }
  },

  isAuthenticated: () => Boolean(localStorage.getItem(TOKEN_KEY)),

  clearSession: clearStoredSession,
};

export const employeeAPI = {
  list: async ({
    page = 1,
    page_size = 100,
    department_id,
    active_only = true,
    search,
  } = {}) => {
    const params = { page, page_size, active_only };

    if (department_id !== undefined && department_id !== null) {
      params.department_id = department_id;
    }

    if (search?.trim()) {
      params.search = search.trim();
    }

    const response = await api.get("/employees/", { params });
    return response.data;
  },

  count: async ({
    department_id,
    active_only = true,
    search,
  } = {}) => {
    const params = { active_only };

    if (department_id !== undefined && department_id !== null) {
      params.department_id = department_id;
    }

    if (search?.trim()) {
      params.search = search.trim();
    }

    const response = await api.get("/employees/count", { params });
    return response.data;
  },
  get: async (employeeId) => {
    const response = await api.get(`/employees/${employeeId}`);
    return response.data;
  },

  create: async (employeeData) => {
    const response = await api.post("/employees/", employeeData);
    return response.data;
  },

  update: async (employeeId, employeeData) => {
    const response = await api.patch(`/employees/${employeeId}`, employeeData);
    return response.data;
  },

  deactivate: async (employeeId) => {
    const response = await api.patch(`/employees/${employeeId}/deactivate`);
    return response.data;
  },
};

export const departmentAPI = {
  list: async ({ include_inactive = false } = {}) => {
    const response = await api.get("/departments/", {
      params: { include_inactive },
    });
    return response.data;
  },

  get: async (departmentId) => {
    const response = await api.get(`/departments/${departmentId}`);
    return response.data;
  },

  create: async (departmentData) => {
    const response = await api.post("/departments/", departmentData);
    return response.data;
  },

  update: async (departmentId, departmentData) => {
    const response = await api.patch(`/departments/${departmentId}`, departmentData);
    return response.data;
  },

  deactivate: async (departmentId) => {
    const response = await api.patch(`/departments/${departmentId}/deactivate`);
    return response.data;
  },
};

export const attritionAPI = {
  history: async (params = {}) => {
    const response = await api.get("/attrition/history", { params });
    return response.data;
  },

  predict: async (employeeData) => {
    const response = await api.post("/attrition/predict", employeeData);
    return response.data;
  },

  train: async () => {
    const response = await api.post("/attrition/train");
    return response.data;
  },
};

export const analyticsAPI = {
  overview: async () => {
    const response = await api.get('/analytics/overview');
    return response.data;
  },
};

export const healthAPI = {
  check: async () => {
    const healthUrl = API_BASE_URL.replace(/\/api\/v1\/?$/, "");
    const response = await axios.get(`${healthUrl}/health`, {
      timeout: 10000,
    });
    return response.data;
  },
};

export const attendanceAPI = {
  getShifts: async () => {
    const response = await api.get("/attendance/shifts");
    return response.data;
  },
  createShift: async (shiftData) => {
    const response = await api.post("/attendance/shifts", shiftData);
    return response.data;
  },
  clockIn: async (data) => {
    const response = await api.post("/attendance/check-in", data);
    return response.data;
  },
  clockOut: async (data) => {
    const response = await api.post("/attendance/check-out", data);
    return response.data;
  },
  list: async (params = {}) => {
    const response = await api.get("/attendance/", { params });
    return response.data;
  },
  summary: async () => {
    const response = await api.get("/attendance/summary");
    return response.data;
  },
};

export const leaveAPI = {
  list: async (params = {}) => {
    const response = await api.get("/leaves/", { params });
    return response.data;
  },
  apply: async (data) => {
    const response = await api.post("/leaves/", data);
    return response.data;
  },
  updateStatus: async (leaveId, data) => {
    const response = await api.patch(`/leaves/${leaveId}/status`, data);
    return response.data;
  },
  balance: async (employeeId, year = 2026) => {
    const response = await api.get(`/leaves/balance/${employeeId}`, {
      params: { year },
    });
    return response.data;
  },
};

export const payrollAPI = {
  list: async (params = {}) => {
    const response = await api.get("/payroll/", { params });
    return response.data;
  },
  generate: async (data) => {
    const response = await api.post("/payroll/generate", data);
    return response.data;
  },
  updateStatus: async (payrollId, data) => {
    const response = await api.patch(`/payroll/${payrollId}/status`, data);
    return response.data;
  },
  summary: async (params = {}) => {
    const response = await api.get("/payroll/summary", { params });
    return response.data;
  },
};

export const notificationAPI = {
  list: async (params = {}) => {
    const response = await api.get("/notifications/", { params });
    return response.data;
  },
  unreadCount: async () => {
    const response = await api.get("/notifications/unread-count");
    return response.data;
  },
  markRead: async (notifId) => {
    const response = await api.patch(`/notifications/${notifId}/read`);
    return response.data;
  },
  markAllRead: async () => {
    const response = await api.patch("/notifications/read-all");
    return response.data;
  },
  create: async (data) => {
    const response = await api.post("/notifications/", data);
    return response.data;
  },
};

export const chatAPI = {
  messages: async (params = {}) => {
    const response = await api.get("/chat/messages", { params });
    return response.data;
  },
  send: async (data) => {
    const response = await api.post("/chat/send", data);
    return response.data;
  },
  contacts: async () => {
    const response = await api.get("/chat/contacts");
    return response.data;
  },
};

export const documentAPI = {
  list: async (params = {}) => {
    const response = await api.get("/documents/", { params });
    return response.data;
  },
  upload: async (data) => {
    const response = await api.post("/documents/", data);
    return response.data;
  },
  delete: async (docId) => {
    const response = await api.delete(`/documents/${docId}`);
    return response.data;
  },
};

export const taskAPI = {
  list: async (params = {}) => {
    const response = await api.get("/tasks/", { params });
    return response.data;
  },
  create: async (data) => {
    const response = await api.post("/tasks/", data);
    return response.data;
  },
  update: async (taskId, data) => {
    const response = await api.patch(`/tasks/${taskId}`, data);
    return response.data;
  },
  delete: async (taskId) => {
    const response = await api.delete(`/tasks/${taskId}`);
    return response.data;
  },
};

export const performanceAPI = {
  list: async (params = {}) => {
    const response = await api.get("/performance/", { params });
    return response.data;
  },
  create: async (data) => {
    const response = await api.post("/performance/", data);
    return response.data;
  },
  summary: async () => {
    const response = await api.get("/performance/summary");
    return response.data;
  },
};

export const reportAPI = {
  workforce: async () => {
    const response = await api.get("/reports/workforce-summary");
    return response.data;
  },
  attendance: async () => {
    const response = await api.get("/reports/attendance-summary");
    return response.data;
  },
  payroll: async () => {
    const response = await api.get("/reports/payroll-summary");
    return response.data;
  },
  attrition: async () => {
    const response = await api.get("/reports/attrition-summary");
    return response.data;
  },
};

export const auditLogAPI = {
  list: async (params = {}) => {
    const response = await api.get("/audit-logs/", { params });
    return response.data;
  },
  create: async (data) => {
    const response = await api.post("/audit-logs/", data);
    return response.data;
  },
};

export const aiMonitoringAPI = {
  highRisk: async () => {
    const response = await api.get("/ai-monitoring/high-risk");
    return response.data;
  },
  recommendations: async () => {
    const response = await api.get("/ai-monitoring/recommendations");
    return response.data;
  },
  stability: async () => {
    const response = await api.get("/ai-monitoring/stability-index");
    return response.data;
  },
};

export { getErrorMessage };

export default api;



