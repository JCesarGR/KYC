import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Camera, AlertTriangle, CheckCircle, XCircle, Shield, Users, Activity, TrendingUp } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Colores para visualizaciones
const COLORS = {
  BAJO: '#10b981',
  MEDIO: '#f59e0b',
  ALTO: '#ef4444',
  CRÍTICO: '#991b1b'
};

const RISK_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#991b1b'];

const KYCDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [checkResults, setCheckResults] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '',
    first_name: '',
    paternal_surname: '',
    maternal_surname: '',
    birth_date: '',
    curp: '',
    rfc: '',
    email: '',
    phone: '',
    address: '',
    state: 'Nacional',
    consent_id: '',
    requested_by: '',
    include_rnd_check: true,
    include_sanctions: true,
    include_enrichment: true,
    include_network_analysis: true
  });

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Actualizar cada 30 segundos
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/stats`);
      const data = await response.json();
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/background-check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      setCheckResults(data);
      setActiveTab('results');
      fetchStats(); // Actualizar estadísticas
    } catch (error) {
      console.error('Error performing background check:', error);
      alert('Error al realizar el background check. Por favor intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeColor = (level) => {
    const colors = {
      'BAJO': 'bg-green-100 text-green-800',
      'MEDIO': 'bg-yellow-100 text-yellow-800',
      'ALTO': 'bg-red-100 text-red-800',
      'CRÍTICO': 'bg-red-900 text-white'
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  const StatCard = ({ title, value, subtitle, icon: Icon, color }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-3xl font-bold mt-2 ${color}`}>{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={`p-3 rounded-full ${color} bg-opacity-10`}>
            <Icon className={`w-8 h-8 ${color}`} />
          </div>
        )}
      </div>
    </div>
  );

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Cargando datos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="w-10 h-10 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">KYC Platform</h1>
                <p className="text-sm text-gray-600">Background Checks & Compliance</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-gray-600">Estado del Sistema</p>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-green-600">Operacional</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`${
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
            >
              <Activity className="w-4 h-4" />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setActiveTab('check')}
              className={`${
                activeTab === 'check'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
            >
              <Camera className="w-4 h-4" />
              <span>Nuevo Check</span>
            </button>
            {checkResults && (
              <button
                onClick={() => setActiveTab('results')}
                className={`${
                  activeTab === 'results'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <CheckCircle className="w-4 h-4" />
                <span>Resultados</span>
              </button>
            )}
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Checks Totales"
                value={stats.total_checks.toLocaleString()}
                subtitle="Todos los tiempos"
                icon={Users}
                color="text-blue-600"
              />
              <StatCard
                title="Checks Hoy"
                value={stats.checks_today}
                subtitle={`Esta semana: ${stats.checks_this_week}`}
                icon={TrendingUp}
                color="text-green-600"
              />
              <StatCard
                title="Alto Riesgo"
                value={stats.high_risk_detections}
                subtitle="Detecciones críticas"
                icon={AlertTriangle}
                color="text-red-600"
              />
              <StatCard
                title="Tiempo Promedio"
                value={`${stats.average_processing_time.toFixed(0)}ms`}
                subtitle="Procesamiento"
                icon={Activity}
                color="text-purple-600"
              />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Risk Distribution */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Distribución de Riesgo
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={Object.entries(stats.risk_distribution).map(([name, value]) => ({
                        name,
                        value
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.keys(stats.risk_distribution).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={RISK_COLORS[index % RISK_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Top Risk Indicators */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Principales Indicadores de Riesgo
                </h3>
                <div className="space-y-3">
                  {stats.top_risk_indicators.map((indicator, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                          <span className="text-red-600 font-semibold text-sm">{index + 1}</span>
                        </div>
                        <span className="text-sm text-gray-700">{indicator.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-red-600 h-2 rounded-full"
                            style={{ width: `${(indicator.count / stats.total_checks) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900">{indicator.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Activity Timeline */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Actividad Reciente
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart
                  data={[
                    { name: 'Lun', checks: 12 },
                    { name: 'Mar', checks: 19 },
                    { name: 'Mié', checks: 15 },
                    { name: 'Jue', checks: 25 },
                    { name: 'Vie', checks: 22 },
                    { name: 'Sáb', checks: 8 },
                    { name: 'Dom', checks: 5 }
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="checks" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* New Check Form Tab */}
        {activeTab === 'check' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">Nuevo Background Check</h2>
              <p className="mt-1 text-sm text-gray-600">
                Complete la información de la persona a verificar
              </p>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Datos Personales */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Datos Personales</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nombre Completo *</label>
                    <input
                      type="text"
                      name="full_name"
                      required
                      value={formData.full_name}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nombre(s) *</label>
                    <input
                      type="text"
                      name="first_name"
                      required
                      value={formData.first_name}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Apellido Paterno *</label>
                    <input
                      type="text"
                      name="paternal_surname"
                      required
                      value={formData.paternal_surname}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Apellido Materno</label>
                    <input
                      type="text"
                      name="maternal_surname"
                      value={formData.maternal_surname}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Fecha de Nacimiento</label>
                    <input
                      type="text"
                      name="birth_date"
                      placeholder="DD/MM/YYYY"
                      value={formData.birth_date}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Identificación */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Identificación</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">CURP</label>
                    <input
                      type="text"
                      name="curp"
                      maxLength="18"
                      value={formData.curp}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 uppercase"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">RFC</label>
                    <input
                      type="text"
                      name="rfc"
                      maxLength="13"
                      value={formData.rfc}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 uppercase"
                    />
                  </div>
                </div>
              </div>

              {/* Contacto */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Datos de Contacto</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Teléfono</label>
                    <input
                      type="tel"
                      name="phone"
                      placeholder="+52 55 1234 5678"
                      value={formData.phone}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700">Dirección</label>
                    <input
                      type="text"
                      name="address"
                      value={formData.address}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Opciones */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Opciones de Verificación</h3>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="include_rnd_check"
                      checked={formData.include_rnd_check}
                      onChange={handleInputChange}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Búsqueda en RND (Detenciones)</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="include_sanctions"
                      checked={formData.include_sanctions}
                      onChange={handleInputChange}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Listas de Sanciones (OFAC, ONU, SAT)</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="include_enrichment"
                      checked={formData.include_enrichment}
                      onChange={handleInputChange}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enriquecimiento de Datos</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="include_network_analysis"
                      checked={formData.include_network_analysis}
                      onChange={handleInputChange}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Análisis de Red</span>
                  </label>
                </div>
              </div>

              {/* Compliance */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Cumplimiento</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">ID de Consentimiento *</label>
                    <input
                      type="text"
                      name="consent_id"
                      required
                      value={formData.consent_id}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Solicitado por *</label>
                    <input
                      type="text"
                      name="requested_by"
                      required
                      value={formData.requested_by}
                      onChange={handleInputChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setFormData({
                    full_name: '',
                    first_name: '',
                    paternal_surname: '',
                    maternal_surname: '',
                    birth_date: '',
                    curp: '',
                    rfc: '',
                    email: '',
                    phone: '',
                    address: '',
                    state: 'Nacional',
                    consent_id: '',
                    requested_by: '',
                    include_rnd_check: true,
                    include_sanctions: true,
                    include_enrichment: true,
                    include_network_analysis: true
                  })}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Limpiar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                >
                  {loading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
                  <span>{loading ? 'Procesando...' : 'Ejecutar Verificación'}</span>
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && checkResults && (
          <div className="space-y-6">
            {/* Header con Score */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {checkResults.subject.full_name}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Check ID: {checkResults.check_id}
                  </p>
                </div>
                <div className="text-right">
                  <div className={`inline-flex px-4 py-2 rounded-lg text-sm font-medium ${getRiskBadgeColor(checkResults.global_risk_level)}`}>
                    Riesgo: {checkResults.global_risk_level}
                  </div>
                  <p className="text-3xl font-bold mt-2">
                    {checkResults.global_risk_score.toFixed(1)}/100
                  </p>
                </div>
              </div>
            </div>

            {/* Alertas Críticas */}
            {checkResults.critical_alerts && checkResults.critical_alerts.length > 0 && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-lg">
                <div className="flex">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Alertas Críticas</h3>
                    <div className="mt-2 space-y-2">
                      {checkResults.critical_alerts.map((alert, index) => (
                        <div key={index} className="text-sm text-red-700">
                          <span className="font-medium">{alert.type}:</span> {alert.message}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Flags */}
            {checkResults.flags && checkResults.flags.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Indicadores</h3>
                <div className="space-y-2">
                  {checkResults.flags.map((flag, index) => (
                    <div key={index} className="flex items-start space-x-2">
                      <span className="text-lg">{flag.split(' ')[0]}</span>
                      <span className="text-sm text-gray-700">{flag.substring(flag.indexOf(' ') + 1)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Resultados Detallados */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* CURP Validation */}
              {checkResults.curp_validation && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Validación CURP</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Válido:</span>
                      <span className={`text-sm font-medium ${checkResults.curp_validation.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                        {checkResults.curp_validation.is_valid ? 'Sí' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Mensaje:</span>
                      <span className="text-sm text-gray-900">{checkResults.curp_validation.message}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Enrichment Results */}
              {checkResults.enrichment_results && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Enriquecimiento</h3>
                  {checkResults.enrichment_results.email && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700">Email</p>
                      <p className="text-sm text-gray-600">
                        Riesgo: {checkResults.enrichment_results.email.risk_level}
                      </p>
                    </div>
                  )}
                  {checkResults.enrichment_results.phone && (
                    <div>
                      <p className="text-sm font-medium text-gray-700">Teléfono</p>
                      <p className="text-sm text-gray-600">
                        Carrier: {checkResults.enrichment_results.phone.carrier || 'N/A'}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Metadata */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Información del Check</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Tiempo de Procesamiento</p>
                  <p className="text-sm font-medium text-gray-900">{checkResults.processing_time_ms.toFixed(0)} ms</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Fuentes Consultadas</p>
                  <p className="text-sm font-medium text-gray-900">{checkResults.sources_consulted.length}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Solicitado por</p>
                  <p className="text-sm font-medium text-gray-900">{checkResults.requested_by}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Fecha</p>
                  <p className="text-sm font-medium text-gray-900">
                    {new Date(checkResults.timestamp).toLocaleString('es-MX')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KYCDashboard;
