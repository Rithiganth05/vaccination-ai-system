import { useState } from "react";

const API = "http://127.0.0.1:8001";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [userId, setUserId] = useState(null);

  const [showRegister, setShowRegister] = useState(false);
  const [registerUsername, setRegisterUsername] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerDob, setRegisterDob] = useState("");
  const [registerGender, setRegisterGender] = useState("");
  const [registerContact, setRegisterContact] = useState("");

  const [dashboard, setDashboard] = useState(null);
  const [records, setRecords] = useState([]);
  const [vaccines, setVaccines] = useState([]);

  const [showAddRecord, setShowAddRecord] = useState(false);
  const [recordVaccineId, setRecordVaccineId] = useState("");
  const [recordDoseNumber, setRecordDoseNumber] = useState("");
  const [recordVaccinationDate, setRecordVaccinationDate] = useState("");
  const [recordNextDueDate, setRecordNextDueDate] = useState("");
  const [recordStatus, setRecordStatus] = useState("");

  const [editingRecordId, setEditingRecordId] = useState(null);
  const [editVaccineId, setEditVaccineId] = useState("");
  const [editDoseNumber, setEditDoseNumber] = useState("");
  const [editVaccinationDate, setEditVaccinationDate] = useState("");
  const [editNextDueDate, setEditNextDueDate] = useState("");
  const [editStatus, setEditStatus] = useState("");

  const api = async (url, options = {}) => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      alert("Please login again");
      throw new Error("No authentication token");
    }

    const response = await fetch(`${API}${url}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }

    return data;
  };

  // Get dashboard
  const getDashboard = async (id) => {
    try {
      setDashboard(await api(`/dashboard/${id}`));
    } catch (error) {
      console.error("Dashboard error:", error);
    }
  };

  // Get vaccination records
  const getVaccinationRecords = async () => {
    try {
      setRecords(await api("/vaccination-records"));
    } catch (error) {
      console.error("Records error:", error);
    }
  };

  // Get vaccines
  const getVaccines = async () => {
    try {
      setVaccines(await api("/vaccines"));
    } catch (error) {
      console.error("Vaccine error:", error);
    }
  };

  const handleAddRecord = async (e) => {
    e.preventDefault();

    if (!userId) {
      alert("User ID not found. Please login again.");
      return;
    }

    const recordData = {
      user_id: userId,
      vaccine_id: Number(recordVaccineId),
      dose_number: Number(recordDoseNumber),
      vaccination_date: recordVaccinationDate,
      next_due_date: recordNextDueDate || null,
      status: recordStatus,
    };

    try {
      await api("/vaccination-records", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(recordData),
      });

      alert("Vaccination record added successfully");

      setRecordVaccineId("");
      setRecordDoseNumber("");
      setRecordVaccinationDate("");
      setRecordNextDueDate("");
      setRecordStatus("");
      setShowAddRecord(false);

      await getVaccinationRecords();
      await getDashboard(userId);
    } catch (error) {
      alert(error.message);
    }
  };

  // Start editing
  const startEditRecord = (record) => {
    setEditingRecordId(record.record_id);
    setEditVaccineId(String(record.vaccine_id));
    setEditDoseNumber(String(record.dose_number));
    setEditVaccinationDate(record.vaccination_date);
    setEditNextDueDate(record.next_due_date || "");
    setEditStatus(record.status);
    setShowAddRecord(false);
  };

  // Cancel editing
  const cancelEditRecord = () => {
    setEditingRecordId(null);
    setEditVaccineId("");
    setEditDoseNumber("");
    setEditVaccinationDate("");
    setEditNextDueDate("");
    setEditStatus("");
  };

  // Update vaccination record
  const handleEditRecord = async (e) => {
    e.preventDefault();

    if (!userId || editingRecordId === null) {
      alert("Please select a valid record.");
      return;
    }

    const recordData = {
      user_id: userId,
      vaccine_id: Number(editVaccineId),
      dose_number: Number(editDoseNumber),
      vaccination_date: editVaccinationDate,
      next_due_date: editNextDueDate || null,
      status: editStatus,
    };

    try {
      await api(`/vaccination-records/${editingRecordId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(recordData),
      });

      alert("Vaccination record updated successfully");

      cancelEditRecord();
      await getVaccinationRecords();
      await getDashboard(userId);
    } catch (error) {
      alert(error.message);
    }
  };

  // Delete vaccination record
  const handleDeleteRecord = async (recordId) => {
    if (
      !window.confirm(
        "Are you sure you want to delete this vaccination record?"
      )
    ) {
      return;
    }

    try {
      await api(`/vaccination-records/${recordId}`, {
        method: "DELETE",
      });

      alert("Vaccination record deleted successfully");

      if (editingRecordId === recordId) {
        cancelEditRecord();
      }

      await getVaccinationRecords();
      await getDashboard(userId);
    } catch (error) {
      alert(error.message);
    }
  };

  // Generate AI prediction
  const handleGeneratePrediction = async () => {
    if (!userId) {
      alert("User ID not found. Please login again.");
      return;
    }

    try {
      await api("/predictions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
        }),
      });

      alert("AI prediction generated successfully");
      await getDashboard(userId);
    } catch (error) {
      alert(error.message);
    }
  };

  // Register
  const handleRegister = async (e) => {
    e.preventDefault();

    const registerData = {
      username: registerUsername.trim(),
      password: registerPassword,
      name: registerName.trim(),
      date_of_birth: registerDob,
      gender: registerGender,
      contact: registerContact.trim(),
    };

    try {
      const response = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(registerData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      alert("Registration successful. Please login.");

      setShowRegister(false);
      setUsername(registerData.username);

      setRegisterUsername("");
      setRegisterPassword("");
      setRegisterName("");
      setRegisterDob("");
      setRegisterGender("");
      setRegisterContact("");
    } catch (error) {
      alert(error.message);
    }
  };

  // Login
  const handleLogin = async (e) => {
    e.preventDefault();

    const formData = new URLSearchParams();
    formData.append("username", username.trim());
    formData.append("password", password);

    try {
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      localStorage.setItem("access_token", data.access_token);
      setUserId(data.user_id);

      alert("Login successful");

      await getDashboard(data.user_id);
      await getVaccinationRecords();
      await getVaccines();
    } catch (error) {
      alert(error.message);
    }
  };

  // Logout
  const handleLogout = () => {
    localStorage.removeItem("access_token");

    setUserId(null);
    setDashboard(null);
    setRecords([]);
    setVaccines([]);

    setUsername("");
    setPassword("");

    setShowAddRecord(false);

    setRecordVaccineId("");
    setRecordDoseNumber("");
    setRecordVaccinationDate("");
    setRecordNextDueDate("");
    setRecordStatus("");

    cancelEditRecord();
  };

  return (
    <div className="app">
      {!dashboard ? (
        <div className="login-container">
          <div className="login-box">
            {!showRegister ? (
              <>
                <h1>Vaccination AI System</h1>
                <h2>Login</h2>

                <form onSubmit={handleLogin}>
                  <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />

                  <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  <button type="submit">Login</button>
                </form>

                <p>
                  New user?{" "}
                  <button
                    type="button"
                    onClick={() => setShowRegister(true)}
                  >
                    Register
                  </button>
                </p>
              </>
            ) : (
              <>
                <h1>Vaccination AI System</h1>
                <h2>Register</h2>

                <form onSubmit={handleRegister}>
                  <input
                    type="text"
                    placeholder="Username"
                    value={registerUsername}
                    onChange={(e) =>
                      setRegisterUsername(e.target.value)
                    }
                    required
                  />

                  <input
                    type="password"
                    placeholder="Password"
                    value={registerPassword}
                    onChange={(e) =>
                      setRegisterPassword(e.target.value)
                    }
                    required
                  />

                  <input
                    type="text"
                    placeholder="Full Name"
                    value={registerName}
                    onChange={(e) =>
                      setRegisterName(e.target.value)
                    }
                    required
                  />

                  <input
                    type="date"
                    value={registerDob}
                    onChange={(e) =>
                      setRegisterDob(e.target.value)
                    }
                    required
                  />

                  <select
                    value={registerGender}
                    onChange={(e) =>
                      setRegisterGender(e.target.value)
                    }
                    required
                  >
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>

                  <input
                    type="text"
                    placeholder="Contact"
                    value={registerContact}
                    onChange={(e) =>
                      setRegisterContact(e.target.value)
                    }
                    required
                  />

                  <button type="submit">Register</button>
                </form>

                <p>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => setShowRegister(false)}
                  >
                    Login
                  </button>
                </p>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="dashboard">
          <h1>Vaccination Dashboard</h1>

          <button onClick={handleLogout}>Logout</button>

          <h2>Welcome, {dashboard.user.name}</h2>

          <div className="user-info">
            <h2>User Information</h2>

            <p>
              <strong>User ID:</strong>{" "}
              {dashboard.user.user_id}
            </p>

            <p>
              <strong>Name:</strong>{" "}
              {dashboard.user.name}
            </p>

            <p>
              <strong>Date of Birth:</strong>{" "}
              {dashboard.user.date_of_birth}
            </p>

            <p>
              <strong>Gender:</strong>{" "}
              {dashboard.user.gender}
            </p>

            <p>
              <strong>Contact:</strong>{" "}
              {dashboard.user.contact}
            </p>
          </div>

          <div className="summary">
            <div className="card">
              <h3>Total Records</h3>
              <p>
                {dashboard.vaccination_summary.total_records}
              </p>
            </div>

            <div className="card">
              <h3>Completed</h3>
              <p>
                {dashboard.vaccination_summary.completed}
              </p>
            </div>

            <div className="card">
              <h3>Missed</h3>
              <p>
                {dashboard.vaccination_summary.missed}
              </p>
            </div>

            <div className="card">
              <h3>Upcoming</h3>
              <p>
                {dashboard.vaccination_summary.upcoming}
              </p>
            </div>

            <div className="card">
              <h3>Overdue</h3>
              <p>
                {dashboard.vaccination_summary.overdue}
              </p>
            </div>
          </div>

          <div className="prediction">
            <h2>AI Risk Prediction</h2>

            <button
              type="button"
              onClick={handleGeneratePrediction}
            >
              Generate AI Prediction
            </button>

            {dashboard.latest_prediction ? (
              <div className="prediction-card">
                <p>
                  <strong>Risk Level:</strong>{" "}
                  {dashboard.latest_prediction.risk_level}
                </p>

                <p>
                  <strong>Missed Probability:</strong>{" "}
                  {dashboard.latest_prediction.missed_probability}%
                </p>

                <div className="risk-bar">
                  <div
                    className="risk-progress"
                    style={{
                      width: `${Math.min(
                        Math.max(
                          dashboard.latest_prediction
                            .missed_probability,
                          0
                        ),
                        100
                      )}%`,
                    }}
                  />
                </div>

                <p>
                  <strong>Prediction Date:</strong>{" "}
                  {new Date(
                    dashboard.latest_prediction.prediction_date
                  ).toLocaleString()}
                </p>
              </div>
            ) : (
              <p>
                No prediction available. Click "Generate AI
                Prediction" to create one.
              </p>
            )}
          </div>

          <div className="records">
            <h2>Vaccination Records</h2>

            <button
              type="button"
              onClick={() => {
                if (editingRecordId !== null) {
                  cancelEditRecord();
                }

                setShowAddRecord(!showAddRecord);
              }}
            >
              {showAddRecord
                ? "Cancel"
                : "Add Vaccination Record"}
            </button>

            {showAddRecord && (
              <form onSubmit={handleAddRecord}>
                <h3>Add Vaccination Record</h3>

                <label>Vaccine:</label>

                <select
                  value={recordVaccineId}
                  onChange={(e) =>
                    setRecordVaccineId(e.target.value)
                  }
                  required
                >
                  <option value="">Select Vaccine</option>

                  {vaccines.map((vaccine) => (
                    <option
                      key={vaccine.vaccine_id}
                      value={vaccine.vaccine_id}
                    >
                      {vaccine.vaccine_name}
                    </option>
                  ))}
                </select>

                <br />

                <label>Dose Number:</label>

                <input
                  type="number"
                  min="1"
                  value={recordDoseNumber}
                  onChange={(e) =>
                    setRecordDoseNumber(e.target.value)
                  }
                  required
                />

                <br />

                <label>Vaccination Date:</label>

                <input
                  type="date"
                  value={recordVaccinationDate}
                  onChange={(e) =>
                    setRecordVaccinationDate(e.target.value)
                  }
                  required
                />

                <br />

                <label>Next Due Date:</label>

                <input
                  type="date"
                  value={recordNextDueDate}
                  onChange={(e) =>
                    setRecordNextDueDate(e.target.value)
                  }
                />

                <br />

                <label>Status:</label>

                <select
                  value={recordStatus}
                  onChange={(e) =>
                    setRecordStatus(e.target.value)
                  }
                  required
                >
                  <option value="">Select Status</option>
                  <option value="Completed">
                    Completed
                  </option>
                  <option value="Missed">
                    Missed
                  </option>
                </select>

                <br />

                <button type="submit">
                  Save Vaccination Record
                </button>
              </form>
            )}

            {editingRecordId !== null && (
              <form onSubmit={handleEditRecord}>
                <h3>Edit Vaccination Record</h3>

                <p>
                  Editing Record ID:{" "}
                  <strong>{editingRecordId}</strong>
                </p>

                <label>Vaccine:</label>

                <select
                  value={editVaccineId}
                  onChange={(e) =>
                    setEditVaccineId(e.target.value)
                  }
                  required
                >
                  <option value="">Select Vaccine</option>

                  {vaccines.map((vaccine) => (
                    <option
                      key={vaccine.vaccine_id}
                      value={vaccine.vaccine_id}
                    >
                      {vaccine.vaccine_name}
                    </option>
                  ))}
                </select>

                <br />

                <label>Dose Number:</label>

                <input
                  type="number"
                  min="1"
                  value={editDoseNumber}
                  onChange={(e) =>
                    setEditDoseNumber(e.target.value)
                  }
                  required
                />

                <br />

                <label>Vaccination Date:</label>

                <input
                  type="date"
                  value={editVaccinationDate}
                  onChange={(e) =>
                    setEditVaccinationDate(e.target.value)
                  }
                  required
                />

                <br />

                <label>Next Due Date:</label>

                <input
                  type="date"
                  value={editNextDueDate}
                  onChange={(e) =>
                    setEditNextDueDate(e.target.value)
                  }
                />

                <br />

                <label>Status:</label>

                <select
                  value={editStatus}
                  onChange={(e) =>
                    setEditStatus(e.target.value)
                  }
                  required
                >
                  <option value="">Select Status</option>
                  <option value="Completed">
                    Completed
                  </option>
                  <option value="Missed">
                    Missed
                  </option>
                </select>

                <br />

                <button type="submit">
                  Update Vaccination Record
                </button>

                <button
                  type="button"
                  onClick={cancelEditRecord}
                >
                  Cancel
                </button>
              </form>
            )}

            {records.length === 0 ? (
              <p>No vaccination records found.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Record ID</th>
                    <th>Vaccine</th>
                    <th>Dose</th>
                    <th>Vaccination Date</th>
                    <th>Next Due Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {records.map((record) => {
                    const vaccine = vaccines.find(
                      (v) =>
                        v.vaccine_id === record.vaccine_id
                    );

                    return (
                      <tr key={record.record_id}>
                        <td>{record.record_id}</td>

                        <td>
                          {vaccine?.vaccine_name || "Unknown"}
                        </td>

                        <td>{record.dose_number}</td>

                        <td>
                          {record.vaccination_date}
                        </td>

                        <td>
                          {record.next_due_date || "-"}
                        </td>

                        <td>{record.status}</td>

                        <td>
                          <button
                            type="button"
                            onClick={() =>
                              startEditRecord(record)
                            }
                          >
                            Edit
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleDeleteRecord(
                                record.record_id
                              )
                            }
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          <div className="reminders">
            <h2>Vaccination Reminders</h2>

            {!dashboard.reminders?.length ? (
              <p>No vaccination reminders.</p>
            ) : (
              dashboard.reminders.map((reminder) => (
                <div
                  className="reminder"
                  key={reminder.record_id}
                >
                  <h3>
                    {reminder.vaccine_name ||
                      "Unknown Vaccine"}
                  </h3>

                  <p>
                    <strong>Dose:</strong>{" "}
                    {reminder.dose_number}
                  </p>

                  <p>
                    <strong>Due Date:</strong>{" "}
                    {reminder.next_due_date}
                  </p>

                  <p>
                    <strong>Status:</strong>{" "}
                    {reminder.status}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;