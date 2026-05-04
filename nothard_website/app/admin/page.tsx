'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Navbar } from "../components/navbar"
import { Footer } from "../components/footer"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { Badge } from "../components/ui/badge"
import { useToast } from "../components/ui/use-toast"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog"

interface User {
  id: number
  telegram_id?: number
  name: string
  phone: string
  email: string
  role: string
  bonuses: number
  language: string
  registration_method: string
  created_at?: string
}

interface Student {
  student_id: number
  first_name: string
  last_name: string
  email: string
  phone: string
  university?: string
  city: string
  agency_name?: string
  created_at: string
}

interface Order {
  order_id: number
  user_id: number
  order_date: string
  status: string
  payment_method: string
  paid: number
  amount: number
  user_name?: string
  user_phone?: string
}

interface Task {
  task_id: number
  description: string
  status: string
  created_at: string
  order_id?: number
  closed_at?: string
  order_user_id?: number
}

interface Income {
  income_id: number
  order_id?: number
  amount: number
  description?: string
  income_date: string
  order_user_id?: number
}

interface Expense {
  expense_id: number
  order_id?: number
  amount: number
  description?: string
  expense_date: string
  order_user_id?: number
}

interface ServiceRequest {
  request_id: number
  student_id: number
  first_name: string
  last_name: string
  student_email: string
  service_name: string
  service_description?: string
  title: string
  description?: string
  status: string
  priority: string
  price?: number
  location?: string
  notes?: string
  agency_name?: string
  runner_name?: string
  created_at: string
  scheduled_date?: string
}

export default function AdminPanel() {
  const [user, setUser] = useState<any>(null)
  const [users, setUsers] = useState<User[]>([])
  const [students, setStudents] = useState<Student[]>([])
  const [serviceRequests, setServiceRequests] = useState<ServiceRequest[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [income, setIncome] = useState<Income[]>([])
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [studentRequests, setStudentRequests] = useState<ServiceRequest[]>([])
  const [showStudentModal, setShowStudentModal] = useState(false)
  const [showEditUserModal, setShowEditUserModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [editUserData, setEditUserData] = useState({
    name: '',
    email: '',
    phone: '',
    role: '',
    bonuses: 0,
    user_id: ''  // Telegram ID
  })
  const [agencies, setAgencies] = useState<any[]>([])
  const [showAddAgencyModal, setShowAddAgencyModal] = useState(false)
  const [newAgencyData, setNewAgencyData] = useState({
    name: '',
    description: '',
    user_name: '',
    user_email: '',
    user_phone: '',
    user_password: ''
  })
  const [selectedAgency, setSelectedAgency] = useState<any>(null)
  const [showEditAgencyModal, setShowEditAgencyModal] = useState(false)
  const [showAgencyPricingModal, setShowAgencyPricingModal] = useState(false)
  const [editAgencyData, setEditAgencyData] = useState({
    name: '',
    description: '',
    user_name: '',
    user_email: '',
    user_phone: ''
  })
  const [agencyPricing, setAgencyPricing] = useState<any[]>([])
  const [customServices, setCustomServices] = useState<any[]>([])
  const [serviceTypes, setServiceTypes] = useState<any[]>([])
  const [selectedRequestStudent, setSelectedRequestStudent] = useState<any>(null)
  const [studentServiceRequests, setStudentServiceRequests] = useState<ServiceRequest[]>([])
  const [showRequestsModal, setShowRequestsModal] = useState(false)
  
  // Состояния для установки индивидуальных цен
  const [showSetPriceModal, setShowSetPriceModal] = useState(false)
  const [selectedService, setSelectedService] = useState<any>(null)
  const [priceData, setPriceData] = useState({
    price_gbp: '',
    price_usd: '',
    price_uzs: ''
  })
  
  const router = useRouter()
  const { toast } = useToast()

  const apiUrl = process.env.NEXT_PUBLIC_API_URL

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = () => {
    const userRole = localStorage.getItem('user_role')
    const userId = localStorage.getItem('user_id')
    const userName = localStorage.getItem('user_name')

    if (!userRole || userRole !== 'admin') {
      toast({
        title: "Доступ запрещен",
        description: "У вас нет прав администратора",
        variant: "destructive",
      })
      router.push('/login')
      return
    }

    setUser({ role: userRole, id: userId, name: userName })
    fetchData(userId || '1') // Используем значение по умолчанию если userId пустой
  }

  const fetchData = async (userId: string) => {
    try {
      setLoading(true)
      
      // Получаем все данные для админа
      const response = await fetch(`${apiUrl}/api/admin/full-data`)
      if (response.ok) {
        const data = await response.json()
        setUsers(data.users || [])
        setStudents(data.students || [])
        setServiceRequests(data.requests || [])
        setOrders(data.orders || [])
        setTasks(data.tasks || [])
        setIncome(data.income || [])
        setExpenses(data.expenses || [])
        setAgencies(data.agencies || [])  // Агентства уже включены в admin/full-data
      } else {
        throw new Error('Failed to fetch admin data')
      }

      // Получаем типы услуг для управления ценами
      const servicesResponse = await fetch(`${apiUrl}/api/service-types`)
      if (servicesResponse.ok) {
        const servicesData = await servicesResponse.json()
        setServiceTypes(servicesData.service_types || [])
      }

    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось загрузить данные",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusMap: { [key: string]: { label: string; variant: any } } = {
      'new': { label: 'Новая', variant: 'default' },
      'assigned': { label: 'Назначена', variant: 'secondary' },
      'in_progress': { label: 'Выполняется', variant: 'outline' },
      'completed': { label: 'Завершена', variant: 'default' },
      'cancelled': { label: 'Отменена', variant: 'destructive' }
    }
    
    const statusInfo = statusMap[status] || { label: status, variant: 'default' }
    return <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
  }

  const getPriorityBadge = (priority: string) => {
    const priorityMap: { [key: string]: { label: string; variant: any } } = {
      'low': { label: 'Низкий', variant: 'secondary' },
      'medium': { label: 'Средний', variant: 'outline' },
      'high': { label: 'Высокий', variant: 'default' },
      'urgent': { label: 'Срочно', variant: 'destructive' }
    }
    
    const priorityInfo = priorityMap[priority] || { label: priority, variant: 'default' }
    return <Badge variant={priorityInfo.variant}>{priorityInfo.label}</Badge>
  }

  const viewStudentDetails = async (student: Student) => {
    try {
      setSelectedStudent(student)
      const response = await fetch(`${apiUrl}/api/service-requests?student_id=${student.student_id}`)
      if (response.ok) {
        const data = await response.json()
        setStudentRequests(data.requests || [])
        setShowStudentModal(true)
      } else {
        throw new Error('Failed to fetch student requests')
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось загрузить заявки студента",
        variant: "destructive",
      })
    }
  }

  const updateUser = async () => {
    if (!selectedUser) return

    try {
      const updateData: any = {}
      
      // Собираем только измененные поля
      if (editUserData.name && editUserData.name !== selectedUser.name) {
        updateData.name = editUserData.name
      }
      if (editUserData.email && editUserData.email !== selectedUser.email) {
        updateData.email = editUserData.email
      }
      if (editUserData.phone && editUserData.phone !== selectedUser.phone) {
        updateData.phone = editUserData.phone
      }
      if (editUserData.role && editUserData.role !== selectedUser.role) {
        updateData.role = editUserData.role
      }
      if (editUserData.bonuses !== selectedUser.bonuses) {
        updateData.bonuses = editUserData.bonuses
      }
      if (editUserData.user_id !== (selectedUser.telegram_id?.toString() || '')) {
        updateData.user_id = editUserData.user_id || null
      }

      if (Object.keys(updateData).length === 0) {
        toast({
          title: "Информация",
          description: "Нет изменений для сохранения",
        })
        return
      }

      const response = await fetch(`${apiUrl}/api/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Данные пользователя обновлены",
        })
        fetchData(user?.id || '1')
        setShowEditUserModal(false)
        setSelectedUser(null)
        setEditUserData({
          name: '',
          email: '',
          phone: '',
          role: '',
          bonuses: 0,
          user_id: ''
        })
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to update user')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось обновить данные пользователя",
        variant: "destructive",
      })
    }
  }

  const openEditUserModal = (user: User) => {
    setSelectedUser(user)
    setEditUserData({
      name: user.name,
      email: user.email,
      phone: user.phone,
      role: user.role,
      bonuses: user.bonuses,
      user_id: user.telegram_id?.toString() || ''
    })
    setShowEditUserModal(true)
  }

  const createAgency = async () => {
    try {
      const { name, description, user_name, user_email, user_phone, user_password } = newAgencyData

      if (!name || !user_name || !user_email || !user_password) {
        toast({
          title: "Ошибка",
          description: "Заполните все обязательные поля",
          variant: "destructive",
        })
        return
      }

      const response = await fetch(`${apiUrl}/api/agencies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description,
          user_name,
          user_email,
          user_phone,
          user_password
        }),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Агентство создано",
        })
        fetchData(user?.id || '1')
        setShowAddAgencyModal(false)
        setNewAgencyData({
          name: '',
          description: '',
          user_name: '',
          user_email: '',
          user_phone: '',
          user_password: ''
        })
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create agency')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось создать агентство",
        variant: "destructive",
      })
    }
  }

  const openEditAgencyModal = (agency: any) => {
    setSelectedAgency(agency)
    setEditAgencyData({
      name: agency.name,
      description: agency.description || '',
      user_name: agency.contact_user_name || '',
      user_email: agency.contact_email || '',
      user_phone: agency.contact_phone || ''
    })
    setShowEditAgencyModal(true)
  }

  const updateAgency = async () => {
    if (!selectedAgency) return

    try {
      const updateData: any = {}
      
      // Собираем только измененные поля
      if (editAgencyData.name && editAgencyData.name !== selectedAgency.name) {
        updateData.name = editAgencyData.name
      }
      if (editAgencyData.description !== (selectedAgency.description || '')) {
        updateData.description = editAgencyData.description
      }
      if (editAgencyData.user_name && editAgencyData.user_name !== (selectedAgency.contact_user_name || '')) {
        updateData.user_name = editAgencyData.user_name
      }
      if (editAgencyData.user_email && editAgencyData.user_email !== (selectedAgency.contact_email || '')) {
        updateData.user_email = editAgencyData.user_email
      }
      if (editAgencyData.user_phone !== (selectedAgency.contact_phone || '')) {
        updateData.user_phone = editAgencyData.user_phone
      }

      if (Object.keys(updateData).length === 0) {
        toast({
          title: "Информация",
          description: "Нет изменений для сохранения",
        })
        return
      }

      const response = await fetch(`${apiUrl}/api/agencies/${selectedAgency.agency_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Данные агентства обновлены",
        })
        fetchData(user?.id || '1')
        setShowEditAgencyModal(false)
        setSelectedAgency(null)
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to update agency')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось обновить данные агентства",
        variant: "destructive",
      })
    }
  }

  const openAgencyPricingModal = async (agency: any) => {
    try {
      setSelectedAgency(agency)
      
      // Загружаем текущие цены агентства
      const response = await fetch(`${apiUrl}/api/agencies/${agency.agency_id}/pricing`)
      if (response.ok) {
        const data = await response.json()
        setAgencyPricing(data.pricing || [])
        setCustomServices(data.custom_services || [])
        setShowAgencyPricingModal(true)
      } else {
        throw new Error('Failed to fetch agency pricing')
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось загрузить цены агентства",
        variant: "destructive",
      })
    }
  }

  // Функция для открытия модального окна установки цены
  const openSetPriceModal = (service: any, agency: any) => {
    setSelectedService(service)
    setSelectedAgency(agency)
    
    // Проверяем, есть ли уже индивидуальная цена для этой услуги
    const existingPrice = agencyPricing.find(p => p.service_type_id === service.service_type_id)
    
    if (existingPrice) {
      setPriceData({
        price_gbp: existingPrice.price_gbp?.toString() || '',
        price_usd: existingPrice.price_usd?.toString() || '',
        price_uzs: existingPrice.price_uzs?.toString() || ''
      })
    } else {
      // Устанавливаем значения по умолчанию на базе стандартных цен
      setPriceData({
        price_gbp: service.price_gbp?.toString() || service.base_price?.toString() || '',
        price_usd: service.price_usd?.toString() || '',
        price_uzs: service.price_uzs?.toString() || ''
      })
    }
    
    setShowSetPriceModal(true)
  }

  // Функция для установки/обновления индивидуальной цены
  const setPriceForAgency = async () => {
    if (!selectedService || !selectedAgency) {
      toast({
        title: "Ошибка",
        description: "Не выбрана услуга или агентство",
        variant: "destructive",
      })
      return
    }

    if (!priceData.price_gbp || !priceData.price_usd) {
      toast({
        title: "Ошибка", 
        description: "Введите цену в фунтах и долларах",
        variant: "destructive",
      })
      return
    }

    try {
      const response = await fetch(`${apiUrl}/api/agencies/${selectedAgency.agency_id}/pricing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          service_type_id: selectedService.service_type_id,
          price_gbp: parseFloat(priceData.price_gbp),
          price_usd: parseFloat(priceData.price_usd),
          price_uzs: priceData.price_uzs ? parseFloat(priceData.price_uzs) : null
        })
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Индивидуальная цена установлена",
        })
        
        // Перезагружаем цены агентства
        const pricingResponse = await fetch(`${apiUrl}/api/agencies/${selectedAgency.agency_id}/pricing`)
        if (pricingResponse.ok) {
          const data = await pricingResponse.json()
          setAgencyPricing(data.pricing || [])
        }
        
        setShowSetPriceModal(false)
        setPriceData({ price_gbp: '', price_usd: '', price_uzs: '' })
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to set price')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось установить цену",
        variant: "destructive",
      })
    }
  }

  const viewRequestDetails = async (student: any) => {
    try {
      setSelectedRequestStudent(student)
      
      // Получаем все заявки для этого студента
      const studentRequests = serviceRequests.filter(request => 
        request.student_id === student.student_id
      )
      
      setStudentServiceRequests(studentRequests)
      setShowRequestsModal(true)
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось загрузить заявки студента",
        variant: "destructive",
      })
    }
  }

  // Функция для группировки заявок по студентам
  const getGroupedRequests = () => {
    const grouped = serviceRequests.reduce((acc, request) => {
      const key = `${request.student_id}`
      if (!acc[key]) {
        acc[key] = {
          student_id: request.student_id,
          first_name: request.first_name,
          last_name: request.last_name,
          student_email: request.student_email,
          requests: []
        }
      }
      acc[key].requests.push(request)
      return acc
    }, {} as any)
    
    return Object.values(grouped)
  }

  const updateRequestStatus = async (requestId: number, newStatus: string) => {
    try {
      const response = await fetch(`${apiUrl}/api/service-requests/${requestId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status: newStatus,
          changed_by: user.id,
          comment: 'Статус изменен администратором'
        }),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Статус заявки обновлен",
        })
        fetchData(user.id) // Обновляем данные
      } else {
        throw new Error('Failed to update status')
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось обновить статус заявки",
        variant: "destructive",
      })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar cartItemsCount={0} onCartClick={() => {}} />
        <main className="flex-grow flex items-center justify-center">
          <div>Загрузка...</div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar cartItemsCount={0} onCartClick={() => {}} />
      <main className="flex-grow bg-gray-100 py-8">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Админ-панель</h1>
            <p className="text-gray-600 mt-2">Добро пожаловать, {user?.name}</p>
          </div>

          {/* Навигация по вкладкам */}
          <div className="flex flex-wrap gap-1 mb-6">
            {[
              { id: 'overview', label: 'Обзор' },
              { id: 'users', label: 'Пользователи' },
              { id: 'agencies', label: 'Агентства' },
              { id: 'students', label: 'Студенты' },
              { id: 'requests', label: 'Заявки' },
              { id: 'orders', label: 'Заказы' },
              { id: 'tasks', label: 'Задачи' },
              { id: 'finance', label: 'Финансы' }
            ].map((tab) => (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? 'default' : 'outline'}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </Button>
            ))}
          </div>

          {/* Обзор */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader>
                  <CardTitle>Всего студентов</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-600">{students.length}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Активные заявки</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-orange-600">
                    {serviceRequests.filter(r => ['new', 'assigned', 'in_progress'].includes(r.status)).length}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Завершенные заявки</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">
                    {serviceRequests.filter(r => r.status === 'completed').length}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Срочные заявки</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-red-600">
                    {serviceRequests.filter(r => r.priority === 'urgent').length}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Пользователи */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Пользователи системы</h2>
              <Card>
                <CardHeader>
                  <CardTitle>Список всех пользователей</CardTitle>
                  <CardDescription>
                    Всего пользователей: {users.length}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">ID</th>
                          <th className="px-6 py-3">Telegram ID</th>
                          <th className="px-6 py-3">Имя</th>
                          <th className="px-6 py-3">Email</th>
                          <th className="px-6 py-3">Телефон</th>
                          <th className="px-6 py-3">Роль</th>
                          <th className="px-6 py-3">Бонусы</th>
                          <th className="px-6 py-3">Регистрация</th>
                          <th className="px-6 py-3">Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((user) => (
                          <tr key={user.id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">
                              {user.id}
                            </td>
                            <td className="px-6 py-4">
                              {user.telegram_id ? (
                                <span className="text-blue-600 font-mono">{user.telegram_id}</span>
                              ) : (
                                <span className="text-gray-400">—</span>
                              )}
                            </td>
                            <td className="px-6 py-4 font-medium">
                              {user.name}
                            </td>
                            <td className="px-6 py-4">{user.email}</td>
                            <td className="px-6 py-4">{user.phone}</td>
                            <td className="px-6 py-4">
                              <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                                {user.role}
                              </Badge>
                            </td>
                            <td className="px-6 py-4">{user.bonuses}</td>
                            <td className="px-6 py-4">
                              <span className={`px-2 py-1 rounded text-xs ${
                                user.registration_method === 'Telegram' 
                                  ? 'bg-blue-100 text-blue-700' 
                                  : 'bg-green-100 text-green-700'
                              }`}>
                                {user.registration_method}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openEditUserModal(user)}
                              >
                                Редактировать
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Агентства */}
          {activeTab === 'agencies' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Управление агентствами</h2>
                <Button onClick={() => setShowAddAgencyModal(true)}>
                  Добавить агентство
                </Button>
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>Список агентств</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">Название</th>
                          <th className="px-6 py-3">Контактное лицо</th>
                          <th className="px-6 py-3">Email</th>
                          <th className="px-6 py-3">Описание</th>
                          <th className="px-6 py-3">Дата создания</th>
                          <th className="px-6 py-3">Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        {agencies.map((agency) => (
                          <tr key={agency.agency_id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">
                              {agency.name}
                            </td>
                            <td className="px-6 py-4">{agency.contact_user_name || 'Не указан'}</td>
                            <td className="px-6 py-4">{agency.contact_email || 'Не указан'}</td>
                            <td className="px-6 py-4">{agency.description || 'Нет описания'}</td>
                            <td className="px-6 py-4">
                              {new Date(agency.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openEditAgencyModal(agency)}
                              >
                                Редактировать
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openAgencyPricingModal(agency)}
                              >
                                Цены
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Студенты */}
          {activeTab === 'students' && (
            <Card>
              <CardHeader>
                <CardTitle>Студенты</CardTitle>
                <CardDescription>Список всех студентов в системе</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">Имя</th>
                          <th className="px-6 py-3">Email</th>
                          <th className="px-6 py-3">Университет</th>
                          <th className="px-6 py-3">Агентство</th>
                          <th className="px-6 py-3">Дата добавления</th>
                          <th className="px-6 py-3">Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                      {students.map((student) => (
                        <tr key={student.student_id} className="bg-white border-b hover:bg-gray-50">
                          <td className="px-6 py-4 font-medium text-gray-900">
                            {student.first_name} {student.last_name}
                          </td>
                          <td className="px-6 py-4">{student.email}</td>
                          <td className="px-6 py-4">{student.university || 'Не указан'}</td>
                          <td className="px-6 py-4">{student.agency_name || 'Прямое обращение'}</td>
                          <td className="px-6 py-4">
                            {new Date(student.created_at).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => viewStudentDetails(student)}
                            >
                              Подробнее
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Заявки */}
          {activeTab === 'requests' && (
            <Card>
              <CardHeader>
                <CardTitle>Заявки на услуги</CardTitle>
                <CardDescription>Заявки сгруппированы по студентам</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                      <tr>
                        <th className="px-6 py-3">Студент</th>
                        <th className="px-6 py-3">Email</th>
                        <th className="px-6 py-3">Количество заявок</th>
                        <th className="px-6 py-3">Последняя заявка</th>
                        <th className="px-6 py-3">Действия</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getGroupedRequests().map((studentGroup: any) => {
                        const latestRequest = studentGroup.requests.sort((a: any, b: any) => 
                          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                        )[0]
                        
                        return (
                          <tr key={studentGroup.student_id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">
                              {studentGroup.first_name} {studentGroup.last_name}
                            </td>
                            <td className="px-6 py-4">{studentGroup.student_email || 'Не указан'}</td>
                            <td className="px-6 py-4">
                              <Badge variant="secondary">
                                {studentGroup.requests.length} заявок
                              </Badge>
                            </td>
                            <td className="px-6 py-4">
                              <div className="space-y-1">
                                <div className="font-medium">{latestRequest.title}</div>
                                <div className="text-xs text-gray-500">
                                  {new Date(latestRequest.created_at).toLocaleDateString()}
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => viewRequestDetails(studentGroup)}
                              >
                                Подробнее ({studentGroup.requests.length})
                              </Button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Аналитика */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Статистика по статусам заявок</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {['new', 'assigned', 'in_progress', 'completed', 'cancelled'].map(status => (
                      <div key={status} className="text-center">
                        <div className="text-2xl font-bold">
                          {serviceRequests.filter(r => r.status === status).length}
                        </div>
                        <div className="text-sm text-gray-600">
                          {getStatusBadge(status)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Статистика по приоритетам</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {['low', 'medium', 'high', 'urgent'].map(priority => (
                      <div key={priority} className="text-center">
                        <div className="text-2xl font-bold">
                          {serviceRequests.filter(r => r.priority === priority).length}
                        </div>
                        <div className="text-sm text-gray-600">
                          {getPriorityBadge(priority)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Заказы */}
          {activeTab === 'orders' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Заказы</h2>
              <Card>
                <CardHeader>
                  <CardTitle>Последние заказы</CardTitle>
                  <CardDescription>
                    Показано: {orders.length} заказов
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">ID заказа</th>
                          <th className="px-6 py-3">Клиент</th>
                          <th className="px-6 py-3">Дата заказа</th>
                          <th className="px-6 py-3">Статус</th>
                          <th className="px-6 py-3">Сумма</th>
                          <th className="px-6 py-3">Оплачен</th>
                          <th className="px-6 py-3">Метод оплаты</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map((order) => (
                          <tr key={order.order_id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">
                              #{order.order_id}
                            </td>
                            <td className="px-6 py-4">
                              <div>
                                <div className="font-medium">{order.user_name || 'Неизвестно'}</div>
                                <div className="text-gray-500 text-sm">{order.user_phone}</div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              {new Date(order.order_date).toLocaleDateString('ru-RU')}
                            </td>
                            <td className="px-6 py-4">
                              <Badge variant={order.status === 'completed' ? 'default' : 'secondary'}>
                                {order.status}
                              </Badge>
                            </td>
                            <td className="px-6 py-4 font-semibold">
                              £{order.amount}
                            </td>
                            <td className="px-6 py-4">
                              {order.paid ? (
                                <Badge variant="default" className="bg-green-500">Да</Badge>
                              ) : (
                                <Badge variant="destructive">Нет</Badge>
                              )}
                            </td>
                            <td className="px-6 py-4">{order.payment_method}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Задачи */}
          {activeTab === 'tasks' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Задачи</h2>
              <Card>
                <CardHeader>
                  <CardTitle>Последние задачи</CardTitle>
                  <CardDescription>
                    Показано: {tasks.length} задач
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">ID</th>
                          <th className="px-6 py-3">Описание</th>
                          <th className="px-6 py-3">Статус</th>
                          <th className="px-6 py-3">Заказ</th>
                          <th className="px-6 py-3">Создано</th>
                          <th className="px-6 py-3">Закрыто</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tasks.map((task) => (
                          <tr key={task.task_id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">
                              #{task.task_id}
                            </td>
                            <td className="px-6 py-4">
                              <div className="max-w-xs truncate">{task.description}</div>
                            </td>
                            <td className="px-6 py-4">
                              <Badge variant={task.status === 'completed' ? 'default' : 'secondary'}>
                                {task.status}
                              </Badge>
                            </td>
                            <td className="px-6 py-4">
                              {task.order_id ? `#${task.order_id}` : '—'}
                            </td>
                            <td className="px-6 py-4">
                              {new Date(task.created_at).toLocaleDateString('ru-RU')}
                            </td>
                            <td className="px-6 py-4">
                              {task.closed_at ? new Date(task.closed_at).toLocaleDateString('ru-RU') : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Финансы */}
          {activeTab === 'finance' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Финансы</h2>
              
              {/* Доходы */}
              <Card>
                <CardHeader>
                  <CardTitle>Доходы</CardTitle>
                  <CardDescription>
                    Последние доходы ({income.length})
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">ID</th>
                          <th className="px-6 py-3">Сумма</th>
                          <th className="px-6 py-3">Описание</th>
                          <th className="px-6 py-3">Заказ</th>
                          <th className="px-6 py-3">Дата</th>
                        </tr>
                      </thead>
                      <tbody>
                        {income.map((item) => (
                          <tr key={item.income_id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">
                              #{item.income_id}
                            </td>
                            <td className="px-6 py-4 font-semibold text-green-600">
                              +£{item.amount}
                            </td>
                            <td className="px-6 py-4">
                              <div className="max-w-xs truncate">{item.description || '—'}</div>
                            </td>
                            <td className="px-6 py-4">
                              {item.order_id ? `#${item.order_id}` : '—'}
                            </td>
                            <td className="px-6 py-4">
                              {new Date(item.income_date).toLocaleDateString('ru-RU')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Расходы */}
              <Card>
                <CardHeader>
                  <CardTitle>Расходы</CardTitle>
                  <CardDescription>
                    Последние расходы ({expenses.length})
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">ID</th>
                          <th className="px-6 py-3">Сумма</th>
                          <th className="px-6 py-3">Описание</th>
                          <th className="px-6 py-3">Заказ</th>
                          <th className="px-6 py-3">Дата</th>
                        </tr>
                      </thead>
                      <tbody>
                        {expenses.map((item) => (
                          <tr key={item.expense_id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900">
                              #{item.expense_id}
                            </td>
                            <td className="px-6 py-4 font-semibold text-red-600">
                              -£{item.amount}
                            </td>
                            <td className="px-6 py-4">
                              <div className="max-w-xs truncate">{item.description || '—'}</div>
                            </td>
                            <td className="px-6 py-4">
                              {item.order_id ? `#${item.order_id}` : '—'}
                            </td>
                            <td className="px-6 py-4">
                              {new Date(item.expense_date).toLocaleDateString('ru-RU')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
      <Footer />
      
      {/* Модальное окно с заявками студента */}
      <Dialog open={showStudentModal} onOpenChange={setShowStudentModal}>
        <DialogContent className="max-w-7xl max-h-[80vh] overflow-y-auto w-full" style={{ maxWidth: '1280px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              Заявки студента: {selectedStudent?.first_name} {selectedStudent?.last_name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <p><strong>Email:</strong> {selectedStudent?.email}</p>
                <p><strong>Телефон:</strong> {selectedStudent?.phone}</p>
                <p><strong>Университет:</strong> {selectedStudent?.university || 'Не указан'}</p>
              </div>
              <div>
                <p><strong>Агентство:</strong> {selectedStudent?.agency_name || 'Прямое обращение'}</p>
                <p><strong>Город:</strong> {selectedStudent?.city || 'Не указан'}</p>
                <p><strong>Дата добавления:</strong> {selectedStudent?.created_at ? new Date(selectedStudent.created_at).toLocaleDateString() : ''}</p>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-3">Заявки на услуги ({studentRequests.length})</h3>
              {studentRequests.length > 0 ? (
                <div className="space-y-3">
                  {studentRequests.map((request) => (
                    <div key={request.request_id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold">{request.title}</h4>
                        {getStatusBadge(request.status)}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{request.service_description}</p>
                      {request.description && (
                        <p className="text-sm mb-2"><strong>Описание:</strong> {request.description}</p>
                      )}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p><strong>Приоритет:</strong> {getPriorityBadge(request.priority)}</p>
                          <p><strong>Цена:</strong> £{request.price}</p>
                        </div>
                        <div>
                          <p><strong>Создано:</strong> {new Date(request.created_at).toLocaleDateString()}</p>
                          <p><strong>Раннер:</strong> {request.runner_name || 'Не назначен'}</p>
                        </div>
                      </div>
                      {request.scheduled_date && (
                        <p className="text-sm mt-2"><strong>Запланировано:</strong> {new Date(request.scheduled_date).toLocaleDateString()}</p>
                      )}
                      {request.location && (
                        <p className="text-sm"><strong>Место:</strong> {request.location}</p>
                      )}
                      {request.notes && (
                        <p className="text-sm"><strong>Заметки:</strong> {request.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">У студента пока нет заявок на услуги</p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно редактирования пользователя */}
      <Dialog open={showEditUserModal} onOpenChange={setShowEditUserModal}>
        <DialogContent className="max-w-6xl w-full" style={{ maxWidth: '1152px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              Редактировать пользователя: {selectedUser?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p><strong>ID:</strong> {selectedUser?.id}</p>
                <p><strong>Регистрация:</strong> {selectedUser?.registration_method}</p>
              </div>
              <div>
                <p><strong>Создан:</strong> {selectedUser?.created_at ? new Date(selectedUser.created_at).toLocaleDateString() : 'Нет данных'}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editName">Имя</Label>
                <Input
                  id="editName"
                  value={editUserData.name}
                  onChange={(e) => setEditUserData(prev => ({...prev, name: e.target.value}))}
                  placeholder="Введите имя"
                />
              </div>
              
              <div>
                <Label htmlFor="editEmail">Email</Label>
                <Input
                  id="editEmail"
                  type="email"
                  value={editUserData.email}
                  onChange={(e) => setEditUserData(prev => ({...prev, email: e.target.value}))}
                  placeholder="Введите email"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editPhone">Телефон</Label>
                <Input
                  id="editPhone"
                  value={editUserData.phone}
                  onChange={(e) => setEditUserData(prev => ({...prev, phone: e.target.value}))}
                  placeholder="Введите телефон"
                />
              </div>
              
              <div>
                <Label htmlFor="editTelegramId">Telegram ID</Label>
                <Input
                  id="editTelegramId"
                  value={editUserData.user_id}
                  onChange={(e) => setEditUserData(prev => ({...prev, user_id: e.target.value}))}
                  placeholder="Введите Telegram ID"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editRole">Роль</Label>
                <Select 
                  onValueChange={(value) => setEditUserData(prev => ({...prev, role: value}))}
                  value={editUserData.role}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Выберите роль" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="student">Student</SelectItem>
                    <SelectItem value="agency">Agency</SelectItem>
                    <SelectItem value="runner">Runner</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="editBonuses">Бонусы</Label>
                <Input
                  id="editBonuses"
                  type="number"
                  value={editUserData.bonuses}
                  onChange={(e) => setEditUserData(prev => ({...prev, bonuses: parseInt(e.target.value) || 0}))}
                  placeholder="Количество бонусов"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowEditUserModal(false)}>
                Отмена
              </Button>
              <Button onClick={updateUser}>
                Сохранить изменения
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно создания агентства */}
      <Dialog open={showAddAgencyModal} onOpenChange={setShowAddAgencyModal}>
        <DialogContent className="max-w-6xl w-full" style={{ maxWidth: '1152px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>Создать новое агентство</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="agencyName">Название агентства *</Label>
                <Input
                  id="agencyName"
                  value={newAgencyData.name}
                  onChange={(e) => setNewAgencyData(prev => ({...prev, name: e.target.value}))}
                  placeholder="Введите название"
                />
              </div>
              
              <div>
                <Label htmlFor="agencyDescription">Описание</Label>
                <Input
                  id="agencyDescription"
                  value={newAgencyData.description}
                  onChange={(e) => setNewAgencyData(prev => ({...prev, description: e.target.value}))}
                  placeholder="Краткое описание"
                />
              </div>
            </div>

            <h3 className="text-lg font-semibold">Контактное лицо</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="agencyUserName">Имя контактного лица *</Label>
                <Input
                  id="agencyUserName"
                  value={newAgencyData.user_name}
                  onChange={(e) => setNewAgencyData(prev => ({...prev, user_name: e.target.value}))}
                  placeholder="Введите имя"
                />
              </div>
              
              <div>
                <Label htmlFor="agencyUserEmail">Email *</Label>
                <Input
                  id="agencyUserEmail"
                  type="email"
                  value={newAgencyData.user_email}
                  onChange={(e) => setNewAgencyData(prev => ({...prev, user_email: e.target.value}))}
                  placeholder="Введите email"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="agencyUserPhone">Телефон</Label>
                <Input
                  id="agencyUserPhone"
                  value={newAgencyData.user_phone}
                  onChange={(e) => setNewAgencyData(prev => ({...prev, user_phone: e.target.value}))}
                  placeholder="Введите телефон"
                />
              </div>
              
              <div>
                <Label htmlFor="agencyUserPassword">Пароль *</Label>
                <Input
                  id="agencyUserPassword"
                  type="password"
                  value={newAgencyData.user_password}
                  onChange={(e) => setNewAgencyData(prev => ({...prev, user_password: e.target.value}))}
                  placeholder="Введите пароль"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAddAgencyModal(false)}>
                Отмена
              </Button>
              <Button onClick={createAgency}>
                Создать агентство
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно редактирования агентства */}
      <Dialog open={showEditAgencyModal} onOpenChange={setShowEditAgencyModal}>
        <DialogContent className="max-w-6xl w-full" style={{ maxWidth: '1152px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              Редактировать агентство: {selectedAgency?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editAgencyName">Название агентства</Label>
                <Input
                  id="editAgencyName"
                  value={editAgencyData.name}
                  onChange={(e) => setEditAgencyData(prev => ({...prev, name: e.target.value}))}
                  placeholder="Введите название"
                />
              </div>
              
              <div>
                <Label htmlFor="editAgencyDescription">Описание</Label>
                <Input
                  id="editAgencyDescription"
                  value={editAgencyData.description}
                  onChange={(e) => setEditAgencyData(prev => ({...prev, description: e.target.value}))}
                  placeholder="Краткое описание"
                />
              </div>
            </div>

            <h3 className="text-lg font-semibold">Контактное лицо</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editAgencyUserName">Имя контактного лица</Label>
                <Input
                  id="editAgencyUserName"
                  value={editAgencyData.user_name}
                  onChange={(e) => setEditAgencyData(prev => ({...prev, user_name: e.target.value}))}
                  placeholder="Введите имя"
                />
              </div>
              
              <div>
                <Label htmlFor="editAgencyUserEmail">Email</Label>
                <Input
                  id="editAgencyUserEmail"
                  type="email"
                  value={editAgencyData.user_email}
                  onChange={(e) => setEditAgencyData(prev => ({...prev, user_email: e.target.value}))}
                  placeholder="Введите email"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editAgencyUserPhone">Телефон</Label>
                <Input
                  id="editAgencyUserPhone"
                  value={editAgencyData.user_phone}
                  onChange={(e) => setEditAgencyData(prev => ({...prev, user_phone: e.target.value}))}
                  placeholder="Введите телефон"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowEditAgencyModal(false)}>
                Отмена
              </Button>
              <Button onClick={updateAgency}>
                Сохранить изменения
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно управления ценами агентства */}
      <Dialog open={showAgencyPricingModal} onOpenChange={setShowAgencyPricingModal}>
        <DialogContent className="max-w-7xl w-full" style={{ maxWidth: '1280px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              Управление ценами: {selectedAgency?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Индивидуальные цены на стандартные услуги</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left border">
                  <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                    <tr>
                      <th className="px-4 py-3">Услуга</th>
                      <th className="px-4 py-3">Стандартная цена</th>
                      <th className="px-4 py-3">Цена для агентства</th>
                      <th className="px-4 py-3">Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {serviceTypes.map((service: any) => {
                      const customPrice = agencyPricing.find(p => p.service_type_id === service.service_type_id)
                      return (
                        <tr key={service.service_type_id} className="border-b">
                          <td className="px-4 py-3">{service.name}</td>
                          <td className="px-4 py-3">
                            {service.price_text || `£${service.price_gbp || service.base_price || 0}`}
                          </td>
                          <td className="px-4 py-3">
                            {customPrice ? (
                              <span className="text-green-600 font-semibold">
                                £{customPrice.price_gbp} (${customPrice.price_usd})
                              </span>
                            ) : (
                              <span className="text-gray-500">Стандартная</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openSetPriceModal(service, selectedAgency)}
                            >
                              {customPrice ? 'Изменить' : 'Установить'}
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-4">Кастомные услуги агентства</h3>
              {customServices.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left border">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                      <tr>
                        <th className="px-4 py-3">Название</th>
                        <th className="px-4 py-3">Описание</th>
                        <th className="px-4 py-3">Цена</th>
                        <th className="px-4 py-3">Действия</th>
                      </tr>
                    </thead>
                    <tbody>
                      {customServices.map((service: any) => (
                        <tr key={service.service_id} className="border-b">
                          <td className="px-4 py-3 font-medium">{service.service_name}</td>
                          <td className="px-4 py-3">{service.description || 'Нет описания'}</td>
                          <td className="px-4 py-3">
                            <span className="text-blue-600 font-semibold">
                              £{service.price_gbp} (${service.price_usd})
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <Button size="sm" variant="outline">
                              Редактировать
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-gray-500">У агентства нет кастомных услуг</p>
              )}
              
              <Button className="mt-4">
                Добавить кастомную услугу
              </Button>
            </div>
            
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => setShowAgencyPricingModal(false)}>
                Закрыть
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно просмотра заявок студента */}
      <Dialog open={showRequestsModal} onOpenChange={setShowRequestsModal}>
        <DialogContent className="max-w-7xl w-full" style={{ maxWidth: '1280px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              Заявки студента: {selectedRequestStudent?.first_name} {selectedRequestStudent?.last_name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p><strong>Email:</strong> {selectedRequestStudent?.student_email || 'Не указан'}</p>
              </div>
              <div>
                <p><strong>Общее количество заявок:</strong> {studentServiceRequests.length}</p>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border">
                <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                  <tr>
                    <th className="px-4 py-3">Услуга</th>
                    <th className="px-4 py-3">Статус</th>
                    <th className="px-4 py-3">Приоритет</th>
                    <th className="px-4 py-3">Раннер</th>
                    <th className="px-4 py-3">Дата создания</th>
                    <th className="px-4 py-3">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {studentServiceRequests.map((request) => (
                    <tr key={request.request_id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium">{request.title}</div>
                          {request.service_description && (
                            <div className="text-xs text-gray-500 mt-1">
                              {request.service_description}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">{getStatusBadge(request.status)}</td>
                      <td className="px-4 py-3">{getPriorityBadge(request.priority)}</td>
                      <td className="px-4 py-3">{request.runner_name || 'Не назначен'}</td>
                      <td className="px-4 py-3">
                        {new Date(request.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <Select 
                          value={request.status}
                          onValueChange={(value) => updateRequestStatus(request.request_id, value)}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="new">Новая</SelectItem>
                            <SelectItem value="assigned">Назначена</SelectItem>
                            <SelectItem value="in_progress">Выполняется</SelectItem>
                            <SelectItem value="completed">Завершена</SelectItem>
                            <SelectItem value="cancelled">Отменена</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div className="flex justify-end">
              <Button variant="outline" onClick={() => setShowRequestsModal(false)}>
                Закрыть
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно установки индивидуальной цены */}
      <Dialog open={showSetPriceModal} onOpenChange={setShowSetPriceModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {agencyPricing.find(p => p.service_type_id === selectedService?.service_type_id) 
                ? 'Изменить индивидуальную цену' 
                : 'Установить индивидуальную цену'
              }
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-2">
                <strong>Агентство:</strong> {selectedAgency?.name}
              </p>
              <p className="text-sm text-gray-600 mb-4">
                <strong>Услуга:</strong> {selectedService?.name || selectedService?.description}
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="price_gbp">Цена в фунтах *</Label>
                <Input
                  id="price_gbp"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={priceData.price_gbp}
                  onChange={(e) => setPriceData(prev => ({ ...prev, price_gbp: e.target.value }))}
                />
              </div>
              
              <div>
                <Label htmlFor="price_usd">Цена в долларах *</Label>
                <Input
                  id="price_usd"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={priceData.price_usd}
                  onChange={(e) => setPriceData(prev => ({ ...prev, price_usd: e.target.value }))}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="price_uzs">Цена в сумах (опционально)</Label>
              <Input
                id="price_uzs"
                type="number"
                step="1000"
                placeholder="0"
                value={priceData.price_uzs}
                onChange={(e) => setPriceData(prev => ({ ...prev, price_uzs: e.target.value }))}
              />
            </div>
            
            {selectedService && (
              <div className="text-sm text-gray-500 bg-gray-50 p-3 rounded">
                <p><strong>Стандартная цена:</strong></p>
                <p>£{selectedService.price_gbp || selectedService.base_price || 0}</p>
                {selectedService.price_usd && <p>${selectedService.price_usd}</p>}
                {selectedService.price_uzs && <p>{selectedService.price_uzs?.toLocaleString()} сум</p>}
              </div>
            )}
            
            <div className="flex justify-end space-x-2 pt-4">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowSetPriceModal(false)
                  setPriceData({ price_gbp: '', price_usd: '', price_uzs: '' })
                }}
              >
                Отмена
              </Button>
              <Button onClick={setPriceForAgency}>
                {agencyPricing.find(p => p.service_type_id === selectedService?.service_type_id) 
                  ? 'Изменить цену' 
                  : 'Установить цену'
                }
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
