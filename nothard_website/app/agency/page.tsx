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

interface Student {
  student_id: number
  first_name: string
  last_name: string
  email: string
  phone: string
  student_email?: string
  student_phone?: string
  university?: string
  city: string
  created_at: string
  date_of_birth?: string
  nationality?: string
  accommodation_type?: string
  budget_min?: number
  budget_max?: number
  archived?: number
  archived_at?: string
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
  payment_status?: string
  price?: number
  location?: string
  notes?: string
  agency_name?: string
  runner_name?: string
  created_at: string
  scheduled_date?: string
}

interface ServiceType {
  service_type_id: number
  name: string
  description: string
  base_price: number
  price: number
  price_gbp: number
  price_usd: number
  price_uzs: number
  price_text: string
  has_custom_price: number
}

export default function AgencyPanel() {
  const [user, setUser] = useState<any>(null)
  const [agencyId, setAgencyId] = useState<number>(0)
  const [students, setStudents] = useState<Student[]>([])
  const [serviceRequests, setServiceRequests] = useState<ServiceRequest[]>([])
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([])
  const [agencyPricing, setAgencyPricing] = useState<any[]>([])
  const [customServices, setCustomServices] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [showAddStudent, setShowAddStudent] = useState(false)
  const [showCreateRequest, setShowCreateRequest] = useState(false)
  const [showPricingModal, setShowPricingModal] = useState(false)
  const [showEditStudentModal, setShowEditStudentModal] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [editStudentData, setEditStudentData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    nationality: '',
    university: ''
  })
  const [showRequestsModal, setShowRequestsModal] = useState(false)
  const [selectedRequestStudent, setSelectedRequestStudent] = useState<any>(null)
  const [studentServiceRequests, setStudentServiceRequests] = useState<ServiceRequest[]>([])
  const [showEditRequestModal, setShowEditRequestModal] = useState(false)
  const [selectedRequest, setSelectedRequest] = useState<ServiceRequest | null>(null)
  const [editRequestData, setEditRequestData] = useState({
    title: '',
    description: '',
    status: '',
    priority: '',
    price: '',
    location: '',
    notes: '',
    scheduled_date: '',
    runner_id: ''
  })
  
  // Состояния для задач
  const [requestTasks, setRequestTasks] = useState<{[key: number]: any[]}>({})
  const [expandedRequests, setExpandedRequests] = useState<{[key: number]: boolean}>({})
  
  // Состояния для недвижимости
  const [taskProperties, setTaskProperties] = useState<{[key: number]: any[]}>({})
  const [showAddPropertyModal, setShowAddPropertyModal] = useState(false)
  const [showEditPropertyModal, setShowEditPropertyModal] = useState(false)
  const [selectedTaskForProperty, setSelectedTaskForProperty] = useState<number | null>(null)
  const [selectedPropertyForEdit, setSelectedPropertyForEdit] = useState<any>(null)
  const [newProperty, setNewProperty] = useState({
    property_url: '',
    property_title: '',
    property_address: '',
    property_rent: '',
    property_description: ''
  })
  const [editProperty, setEditProperty] = useState({
    property_url: '',
    property_title: '',
    property_address: '',
    property_rent: '',
    property_description: '',
    agent_notes: ''
  })
  
  // Состояния для архива
  const [showArchive, setShowArchive] = useState(false)
  const [archivedStudents, setArchivedStudents] = useState<Student[]>([])
  const [showArchivedStudentModal, setShowArchivedStudentModal] = useState(false)
  const [selectedArchivedStudent, setSelectedArchivedStudent] = useState<Student | null>(null)
  const [archivedStudentRequests, setArchivedStudentRequests] = useState<ServiceRequest[]>([])
  
  const router = useRouter()
  const { toast } = useToast()

  const apiUrl = process.env.NEXT_PUBLIC_API_URL

  // Форма для нового студента
  const [studentForm, setStudentForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    nationality: '',
    passport_number: '',
    university: '',
    start_date: '',
    end_date: '',
    emergency_contact: '',
    emergency_phone: '',
    telegram_username: ''
  })

  // Форма для новой заявки
  const [requestForm, setRequestForm] = useState({
    student_id: '',
    service_type_id: '',
    title: '',
    description: '',
    priority: 'medium',
    price: '',
    scheduled_date: '',
    location: '',
    notes: ''
  })

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = () => {
    const userRole = localStorage.getItem('user_role')
    const userId = localStorage.getItem('user_id')
    const userName = localStorage.getItem('user_name')

    if (!userRole || userRole !== 'agency') {
      toast({
        title: "Доступ запрещен",
        description: "У вас нет прав агентства",
        variant: "destructive",
      })
      router.push('/login')
      return
    }

    setUser({ role: userRole, id: userId, name: userName })
    // Для демо используем агентство с ID 1
    setAgencyId(1)
    fetchData(userId || '1', 1)
  }

  const fetchData = async (userId: string, agencyId: number) => {
    try {
      setLoading(true)
      
      // Получаем студентов агентства
      const studentsResponse = await fetch(`${apiUrl}/api/students?user_role=agency&user_id=${userId}&agency_id=${agencyId}`)
      if (studentsResponse.ok) {
        const studentsData = await studentsResponse.json()
        setStudents(studentsData.students || [])
      }

      // Получаем заявки агентства
      const requestsResponse = await fetch(`${apiUrl}/api/service-requests?user_role=agency&user_id=${userId}&agency_id=${agencyId}`)
      if (requestsResponse.ok) {
        const requestsData = await requestsResponse.json()
        setServiceRequests(requestsData.requests || [])
      }

      // Получаем типы услуг с индивидуальными ценами для агентства
      const serviceTypesResponse = await fetch(`${apiUrl}/api/service-types?agency_id=${agencyId}`)
      if (serviceTypesResponse.ok) {
        const serviceTypesData = await serviceTypesResponse.json()
        setServiceTypes(serviceTypesData.service_types || [])
      }

      // Получаем индивидуальные цены агентства
      const pricingResponse = await fetch(`${apiUrl}/api/agency-pricing?agency_id=${agencyId}`)
      if (pricingResponse.ok) {
        const pricingData = await pricingResponse.json()
        setAgencyPricing(pricingData.agency_pricing || [])
      }

      // Получаем кастомные услуги агентства
      const customServicesResponse = await fetch(`${apiUrl}/api/custom-services?agency_id=${agencyId}`)
      if (customServicesResponse.ok) {
        const customServicesData = await customServicesResponse.json()
        setCustomServices(customServicesData.custom_services || [])
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

  const addStudent = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch(`${apiUrl}/api/students`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...studentForm,
          agency_id: agencyId
        }),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Студент добавлен",
        })
        setShowAddStudent(false)
        setStudentForm({
          first_name: '', last_name: '', email: '', phone: '', date_of_birth: '',
          nationality: '', passport_number: '', university: '',
          start_date: '', end_date: '', emergency_contact: '', emergency_phone: '',
          telegram_username: ''
        })
        fetchData(user.id, agencyId) // Обновляем данные
      } else {
        throw new Error('Failed to add student')
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось добавить студента",
        variant: "destructive",
      })
    }
  }

  const openEditStudentModal = (student: Student) => {
    setSelectedStudent(student)
    setEditStudentData({
      first_name: student.first_name,
      last_name: student.last_name,
      email: student.email,
      phone: student.phone,
      date_of_birth: student.date_of_birth || '',
      nationality: student.nationality || '',
      university: student.university || ''
    })
    setShowEditStudentModal(true)
  }

  const updateStudent = async () => {
    if (!selectedStudent) return

    try {
      const updateData: any = {}
      
      // Собираем только измененные поля
      if (editStudentData.first_name && editStudentData.first_name !== selectedStudent.first_name) {
        updateData.first_name = editStudentData.first_name
      }
      if (editStudentData.last_name !== selectedStudent.last_name) {
        updateData.last_name = editStudentData.last_name
      }
      if (editStudentData.email !== selectedStudent.email) {
        updateData.email = editStudentData.email
      }
      if (editStudentData.phone !== selectedStudent.phone) {
        updateData.phone = editStudentData.phone
      }
      if (editStudentData.date_of_birth !== (selectedStudent.date_of_birth || '')) {
        updateData.date_of_birth = editStudentData.date_of_birth || null
      }
      if (editStudentData.nationality !== (selectedStudent.nationality || '')) {
        updateData.nationality = editStudentData.nationality
      }
      if (editStudentData.university !== (selectedStudent.university || '')) {
        updateData.university = editStudentData.university
      }

      if (Object.keys(updateData).length === 0) {
        toast({
          title: "Информация",
          description: "Нет изменений для сохранения",
        })
        return
      }

      const response = await fetch(`${apiUrl}/api/students/${selectedStudent.student_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Данные студента обновлены",
        })
        setShowEditStudentModal(false)
        setSelectedStudent(null)
        fetchData(user.id, agencyId) // Обновляем данные
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to update student')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось обновить данные студента",
        variant: "destructive",
      })
    }
  }

  // Функция для удаления студента
  const deleteStudent = async (student: Student) => {
    if (!confirm(`Вы уверены, что хотите удалить студента ${student.first_name} ${student.last_name}?`)) {
      return
    }

    try {
      const response = await fetch(`${apiUrl}/api/students/${student.student_id}`, {
        method: 'DELETE',
      })

      const result = await response.json()

      if (response.ok) {
        toast({
          title: "Успешно",
          description: result.message,
        })
        fetchData(user.id, agencyId) // Перезагружаем данные
      } else {
        throw new Error(result.error || 'Не удалось удалить студента')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось удалить студента",
        variant: "destructive",
      })
    }
  }

  // Функция для удаления заявки
  const deleteRequest = async (requestId: number) => {
    if (!confirm('Вы уверены, что хотите удалить эту заявку?')) {
      return false
    }

    try {
      const response = await fetch(`${apiUrl}/api/service-requests/${requestId}`, {
        method: 'DELETE',
      })

      const result = await response.json()

      if (response.ok) {
        toast({
          title: "Успешно",
          description: result.message,
        })
        fetchData(user.id, agencyId) // Перезагружаем данные
        return true
      } else {
        throw new Error(result.error || 'Не удалось удалить заявку')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось удалить заявку",
        variant: "destructive",
      })
      return false
    }
  }

  // Функция для открытия модального окна редактирования заявки
  const openEditRequestModal = (request: ServiceRequest) => {
    setSelectedRequest(request)
    setEditRequestData({
      title: request.title || '',
      description: request.description || '',
      status: request.status || '',
      priority: request.priority || '',
      price: request.price?.toString() || '',
      location: request.location || '',
      notes: request.notes || '',
      scheduled_date: request.scheduled_date ? request.scheduled_date.slice(0, 16) : '',
      runner_id: ''
    })
    setShowEditRequestModal(true)
  }

  // Функция для обновления заявки
  const updateRequest = async () => {
    if (!selectedRequest) return

    try {
      const requestData = {
        ...editRequestData,
        price: editRequestData.price ? parseFloat(editRequestData.price) : null,
        runner_id: editRequestData.runner_id || null
      }

      const response = await fetch(`${apiUrl}/api/service-requests/${selectedRequest.request_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      const result = await response.json()

      if (response.ok) {
        toast({
          title: "Успешно",
          description: result.message,
        })
        setShowEditRequestModal(false)
        fetchData(user.id, agencyId) // Перезагружаем данные
        
        // Обновляем локальный список заявок студента
        const updatedRequests = studentServiceRequests.map(req => 
          req.request_id === selectedRequest.request_id 
            ? { ...req, ...requestData, price: requestData.price || req.price }
            : req
        )
        setStudentServiceRequests(updatedRequests)
      } else {
        throw new Error(result.error || 'Не удалось обновить заявку')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось обновить заявку",
        variant: "destructive",
      })
    }
  }

  // Функция для загрузки задач заявки
  const fetchRequestTasks = async (requestId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/service-requests/${requestId}/tasks`)
      const result = await response.json()
      
      if (response.ok) {
        setRequestTasks(prev => ({
          ...prev,
          [requestId]: result.tasks || []
        }))
        return result.tasks || []
      }
    } catch (error) {
      console.error('Fetch tasks error:', error)
    }
    return []
  }

  // Функция для обновления статуса задачи
  const updateTaskStatus = async (taskId: number, status: string, requestId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/tasks/${taskId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      })

      const result = await response.json()

      if (response.ok) {
        // Обновляем локальные задачи
        setRequestTasks(prev => ({
          ...prev,
          [requestId]: prev[requestId]?.map(task => 
            task.task_id === taskId ? { ...task, status } : task
          ) || []
        }))
        
        toast({
          title: "Успешно",
          description: "Статус задачи обновлен",
        })

        // Проверяем, нужно ли автоматически завершить заявку
        await checkAutoCompleteRequest(requestId)
      } else {
        toast({
          title: "Ошибка",
          description: result.error || 'Не удалось обновить статус задачи',
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error('Update task status error:', error)
      toast({
        title: "Ошибка",
        description: 'Произошла ошибка при обновлении статуса задачи',
        variant: "destructive",
      })
    }
  }

  // Функция для обновления статуса оплаты заявки
  const updatePaymentStatus = async (requestId: number, paymentStatus: string) => {
    try {
      const response = await fetch(`${apiUrl}/api/service-requests/${requestId}/payment-status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ payment_status: paymentStatus }),
      })

      const result = await response.json()

      if (response.ok) {
        // Обновляем локальные заявки студента
        setStudentServiceRequests(prev => 
          prev.map(request => 
            request.request_id === requestId 
              ? { ...request, payment_status: paymentStatus }
              : request
          )
        )
        
        const statusText = paymentStatus === 'paid' ? 'оплачено' : 
                          paymentStatus === 'partial' ? 'частично оплачено' : 'не оплачено'
        
        toast({
          title: "Успешно",
          description: `Статус оплаты изменен на "${statusText}"`,
        })
      } else {
        toast({
          title: "Ошибка", 
          description: result.error || 'Не удалось обновить статус оплаты',
          variant: "destructive",
        })
      }
    } catch (error) {
      console.error('Update payment status error:', error)
      toast({
        title: "Ошибка",
        description: "Произошла ошибка при обновлении статуса оплаты",
        variant: "destructive",
      })
    }
  }

  // Функция для проверки автоматического завершения заявки
  const checkAutoCompleteRequest = async (requestId: number) => {
    const tasks = requestTasks[requestId] || []
    if (tasks.length === 0) return

    // Проверяем, все ли задачи выполнены или отменены
    const allTasksCompleted = tasks.every(task => 
      task.status === 'completed' || task.status === 'cancelled'
    )

    if (allTasksCompleted) {
      try {
        const response = await fetch(`${apiUrl}/api/service-requests/${requestId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ status: 'completed' }),
        })

        if (response.ok) {
          // Обновляем локальные данные
          setStudentServiceRequests(prev => 
            prev.map(req => 
              req.request_id === requestId 
                ? { ...req, status: 'completed' }
                : req
            )
          )
          
          toast({
            title: "Заявка завершена",
            description: "Все задачи выполнены, заявка автоматически завершена",
          })

          // Обновляем общий список заявок
          fetchData(user.id, agencyId)
          
          // Проверяем, нужно ли архивировать студента
          await checkArchiveStudent()
        }
      } catch (error) {
        console.error('Auto complete request error:', error)
      }
    }
  }

  // Функция для ручного завершения заявки
  const completeRequestManually = async (requestId: number) => {
    if (window.confirm('Вы уверены, что хотите завершить эту заявку?')) {
      try {
        const response = await fetch(`${apiUrl}/api/service-requests/${requestId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ status: 'completed' }),
        })

        if (response.ok) {
          // Обновляем локальные данные
          setStudentServiceRequests(prev => 
            prev.map(req => 
              req.request_id === requestId 
                ? { ...req, status: 'completed' }
                : req
            )
          )
          
          toast({
            title: "Заявка завершена",
            description: "Заявка успешно завершена",
          })

          fetchData(user.id, agencyId) // Перезагружаем данные
          await checkArchiveStudent()
        }
      } catch (error) {
        console.error('Complete request error:', error)
        toast({
          title: "Ошибка",
          description: 'Произошла ошибка при завершении заявки',
          variant: "destructive",
        })
      }
    }
  }

  // Функция для отмены завершения заявки
  const uncompleteRequest = async (requestId: number) => {
    if (window.confirm('Вы уверены, что хотите отменить завершение этой заявки? Она станет активной снова.')) {
      try {
        const response = await fetch(`${apiUrl}/api/service-requests/${requestId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ status: 'in_progress' }),
        })

        if (response.ok) {
          // Обновляем локальные данные
          setStudentServiceRequests(prev => 
            prev.map(req => 
              req.request_id === requestId 
                ? { ...req, status: 'in_progress' }
                : req
            )
          )
          
          toast({
            title: "Завершение отменено",
            description: "Заявка снова стала активной",
          })

          fetchData(user.id, agencyId) // Перезагружаем данные
        }
      } catch (error) {
        console.error('Uncomplete request error:', error)
        toast({
          title: "Ошибка",
          description: 'Произошла ошибка при отмене завершения заявки',
          variant: "destructive",
        })
      }
    }
  }

  // Функция для проверки архивирования студента
  const checkArchiveStudent = async () => {
    // Проверяем активные заявки студента
    if (selectedRequestStudent && studentServiceRequests.length > 0) {
      const activeRequests = studentServiceRequests.filter(req => 
        req.status !== 'completed' && req.status !== 'cancelled'
      )

      if (activeRequests.length === 0) {
        // Все заявки завершены, можно архивировать
        toast({
          title: "Студент готов к архивированию",
          description: `У студента ${selectedRequestStudent.first_name} ${selectedRequestStudent.last_name} все заявки завершены. Студент может быть перемещен в архив.`,
          variant: "default",
        })
      }
    }
  }

  // Функция для архивации студента
  const archiveStudent = async (studentId: number) => {
    if (!confirm('Вы уверены, что хотите архивировать этого студента? Студент будет перемещен в архив.')) {
      return
    }

    try {
      const response = await fetch(`${apiUrl}/api/students/${studentId}/archive`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const result = await response.json()

      if (response.ok) {
        toast({
          title: "Студент архивирован",
          description: result.message,
        })
        
        // Перезагружаем данные
        fetchData(user.id, agencyId)
        setShowRequestsModal(false)
      } else {
        throw new Error(result.error || 'Не удалось архивировать студента')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось архивировать студента",
        variant: "destructive",
      })
    }
  }

  // Функция для загрузки архивированных студентов
  const fetchArchivedStudents = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/students/archived?agency_id=${agencyId}`)
      if (response.ok) {
        const data = await response.json()
        setArchivedStudents(data.students || [])
      }
    } catch (error) {
      console.error('Error fetching archived students:', error)
    }
  }

  // Функция для разархивации студента
  const unarchiveStudent = async (studentId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/students/${studentId}/unarchive`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const result = await response.json()

      if (response.ok) {
        toast({
          title: "Студент восстановлен",
          description: result.message,
        })
        
        // Перезагружаем данные
        fetchData(user.id, agencyId)
        fetchArchivedStudents()
      } else {
        throw new Error(result.error || 'Не удалось восстановить студента')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось восстановить студента",
        variant: "destructive",
      })
    }
  }

  // Функция для просмотра заявок архивированного студента
  const viewArchivedStudentRequests = async (student: Student) => {
    try {
      setSelectedArchivedStudent(student)
      
      const response = await fetch(`${apiUrl}/api/students/${student.student_id}/requests/archived`)
      if (response.ok) {
        const data = await response.json()
        setArchivedStudentRequests(data.requests || [])
        setShowArchivedStudentModal(true)
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Не удалось загрузить заявки архивированного студента')
      }
    } catch (error: any) {
      toast({
        title: "Ошибка",
        description: error.message || "Не удалось загрузить заявки архивированного студента",
        variant: "destructive",
      })
    }
  }

  // Функции для работы с недвижимостью
  const fetchTaskProperties = async (taskId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/tasks/${taskId}/properties`)
      const result = await response.json()
      
      if (response.ok) {
        setTaskProperties(prev => ({
          ...prev,
          [taskId]: result.properties || []
        }))
        return result.properties || []
      }
    } catch (error) {
      console.error('Fetch properties error:', error)
    }
    return []
  }

  const addProperty = async (taskId: number) => {
    if (!newProperty.property_url.trim()) {
      toast({
        title: "Ошибка",
        description: "URL недвижимости обязателен",
        variant: "destructive",
      })
      return
    }

    try {
      const response = await fetch(`${apiUrl}/api/tasks/${taskId}/properties`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newProperty),
      })

      if (response.ok) {
        toast({
          title: "Успех",
          description: "Объект недвижимости добавлен",
        })
        
        // Обновляем список недвижимости
        await fetchTaskProperties(taskId)
        
        // Сбрасываем форму
        setNewProperty({
          property_url: '',
          property_title: '',
          property_address: '',
          property_rent: '',
          property_description: ''
        })
        setShowAddPropertyModal(false)
        setSelectedTaskForProperty(null)
      } else {
        const errorData = await response.json()
        toast({
          title: "Ошибка",
          description: errorData.error,
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось добавить объект недвижимости",
        variant: "destructive",
      })
    }
  }

  // Функция для открытия модала редактирования недвижимости
  const openEditPropertyModal = (property: any) => {
    setSelectedPropertyForEdit(property)
    setEditProperty({
      property_url: property.property_url || '',
      property_title: property.property_title || '',
      property_address: property.property_address || '',
      property_rent: property.property_rent || '',
      property_description: property.property_description || '',
      agent_notes: property.agent_notes || ''
    })
    setShowEditPropertyModal(true)
  }

  // Функция для обновления недвижимости
  const updateProperty = async () => {
    if (!editProperty.property_url.trim()) {
      toast({
        title: "Ошибка",
        description: "URL недвижимости обязателен",
        variant: "destructive",
      })
      return
    }

    if (!selectedPropertyForEdit) return

    try {
      const response = await fetch(`${apiUrl}/api/properties/${selectedPropertyForEdit.property_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editProperty),
      })

      if (response.ok) {
        toast({
          title: "Успех",
          description: "Информация о недвижимости обновлена",
        })
        
        // Обновляем список недвижимости для всех задач
        const taskId = selectedPropertyForEdit.task_id
        if (taskId) {
          await fetchTaskProperties(taskId)
        }
        
        // Закрываем модал
        setShowEditPropertyModal(false)
        setSelectedPropertyForEdit(null)
        setEditProperty({
          property_url: '',
          property_title: '',
          property_address: '',
          property_rent: '',
          property_description: '',
          agent_notes: ''
        })
      } else {
        const errorData = await response.json()
        toast({
          title: "Ошибка",
          description: errorData.error || 'Не удалось обновить недвижимость',
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось обновить объект недвижимости",
        variant: "destructive",
      })
    }
  }

  const updatePropertyStatus = async (propertyId: number, status: string, taskId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/properties/${propertyId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      })

      if (response.ok) {
        toast({
          title: "Успех",
          description: "Статус объекта недвижимости обновлен",
        })
        
        // Обновляем список недвижимости
        await fetchTaskProperties(taskId)
      } else {
        const errorData = await response.json()
        toast({
          title: "Ошибка",
          description: errorData.error,
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось обновить статус",
        variant: "destructive",
      })
    }
  }

  const selectPropertyForViewing = async (propertyId: number, isSelected: boolean, taskId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/properties/${propertyId}/select-viewing`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_selected: isSelected }),
      })

      if (response.ok) {
        toast({
          title: "Успех",
          description: isSelected ? "Объект выбран для просмотра" : "Объект исключен из просмотра",
        })
        
        // Обновляем список недвижимости
        await fetchTaskProperties(taskId)
      } else {
        const errorData = await response.json()
        toast({
          title: "Ошибка",
          description: errorData.error,
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось обновить выбор для просмотра",
        variant: "destructive",
      })
    }
  }

  // Функция для сортировки услуг в порядке лендинга
  const sortServicesByLandingOrder = (services: ServiceType[]) => {
    // Порядок услуг как на лендинге (точные названия из базы данных)
    const landingOrder = [
      // Пакеты
      'Пакет "Встреть меня"',
      'Пакет "Жилье"', 
      'Премиум пакет',
      // Индивидуальные услуги (в порядке лендинга)
      'Встреча в аэропорту + транспорт (общественный)',
      'Встреча в аэропорту + частный трансфер (такси)',
      'SIM-карта',
      'Oyster-карта',
      'Поиск и подбор жилья',
      'Помощь с временным жильём',
      'Перевозка вещей',
      'Регистрация в Local GP (NHS)',
      'Поддержка на первые 7 дней (9:00–17:00)',
      'Оценка района проживания',
      'Подключение коммунальных услуг',
      'Помощь с открытием счёта (онлайн-банкинг)',
      'Перевод и помощь с договором аренды',
      'Перевод документов'
    ]

    return services.sort((a, b) => {
      const indexA = landingOrder.findIndex(item => a.name.includes(item) || a.description.includes(item))
      const indexB = landingOrder.findIndex(item => b.name.includes(item) || b.description.includes(item))
      
      // Если услуга найдена в порядке лендинга, используем этот индекс
      if (indexA !== -1 && indexB !== -1) {
        return indexA - indexB
      }
      
      // Если только одна найдена, она идет первой
      if (indexA !== -1) return -1
      if (indexB !== -1) return 1
      
      // Если обе не найдены, сортируем по алфавиту
      return a.name.localeCompare(b.name)
    })
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
          student_email: request.student_email || '',
          requests: []
        }
      }
      acc[key].requests.push(request)
      return acc
    }, {} as any)
    
    return Object.values(grouped)
  }

  const viewRequestDetails = async (student: any) => {
    try {
      setSelectedRequestStudent(student)
      
      // Получаем все заявки для этого студента
      const studentRequests = serviceRequests.filter(request => 
        request.student_id === student.student_id
      )
      
      setStudentServiceRequests(studentRequests)
      
      // Загружаем задачи для каждой заявки
      for (const request of studentRequests) {
        const tasks = await fetchRequestTasks(request.request_id)
        
        // Загружаем недвижимость для жилищных задач
        if (tasks && tasks.length > 0) {
          for (const task of tasks) {
            const isHousingTask = task.service_name && (
              task.service_name.includes('жилье') || 
              task.service_name.includes('Жилье') ||
              task.service_name.includes('подбор')
            )
            
            if (isHousingTask) {
              await fetchTaskProperties(task.task_id)
            }
          }
        }
      }
      
      setShowRequestsModal(true)
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось загрузить заявки студента",
        variant: "destructive",
      })
    }
  }

  const createServiceRequest = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch(`${apiUrl}/api/service-requests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...requestForm,
          agency_id: agencyId,
          created_by: user.id
        }),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Заявка создана",
        })
        setShowCreateRequest(false)
        setRequestForm({
          student_id: '', service_type_id: '', title: '', description: '',
          priority: 'medium', price: '', scheduled_date: '', location: '', notes: ''
        })
        fetchData(user.id, agencyId) // Обновляем данные
      } else {
        throw new Error('Failed to create request')
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось создать заявку",
        variant: "destructive",
      })
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
            <h1 className="text-3xl font-bold text-gray-900">Панель агентства</h1>
            <p className="text-gray-600 mt-2">Добро пожаловать, {user?.name}</p>
          </div>

          {/* Навигация по вкладкам */}
          <div className="flex space-x-1 mb-6">
            {[
              { id: 'overview', label: 'Обзор' },
              { id: 'students', label: 'Студенты' },
              { id: 'requests', label: 'Заявки' },
              { id: 'pricing', label: 'Цены' },
              { id: 'archive', label: '📁 Архив' }
            ].map((tab) => (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? 'default' : 'outline'}
                onClick={() => {
                  setActiveTab(tab.id)
                  if (tab.id === 'archive') {
                    fetchArchivedStudents()
                  }
                }}
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
                  <CardTitle>Мои студенты</CardTitle>
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

          {/* Студенты */}
          {activeTab === 'students' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Мои студенты</h2>
                <Button onClick={() => setShowAddStudent(true)}>
                  Добавить студента
                </Button>
              </div>

              {showAddStudent && (
                <Card>
                  <CardHeader>
                    <CardTitle>Добавить нового студента</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={addStudent} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="first_name">Имя *</Label>
                          <Input
                            id="first_name"
                            value={studentForm.first_name}
                            onChange={(e) => setStudentForm({...studentForm, first_name: e.target.value})}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="last_name">Фамилия *</Label>
                          <Input
                            id="last_name"
                            value={studentForm.last_name}
                            onChange={(e) => setStudentForm({...studentForm, last_name: e.target.value})}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="email">Email</Label>
                          <Input
                            id="email"
                            type="email"
                            value={studentForm.email}
                            onChange={(e) => setStudentForm({...studentForm, email: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="phone">Телефон</Label>
                          <Input
                            id="phone"
                            value={studentForm.phone}
                            onChange={(e) => setStudentForm({...studentForm, phone: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="university">Университет</Label>
                          <Input
                            id="university"
                            value={studentForm.university}
                            onChange={(e) => setStudentForm({...studentForm, university: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="nationality">Гражданство</Label>
                          <Input
                            id="nationality"
                            value={studentForm.nationality}
                            onChange={(e) => setStudentForm({...studentForm, nationality: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="date_of_birth">Дата рождения</Label>
                          <Input
                            id="date_of_birth"
                            type="date"
                            value={studentForm.date_of_birth}
                            onChange={(e) => setStudentForm({...studentForm, date_of_birth: e.target.value})}
                          />
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button type="submit">Добавить студента</Button>
                        <Button type="button" variant="outline" onClick={() => setShowAddStudent(false)}>
                          Отмена
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                          <th className="px-6 py-3">Имя</th>
                          <th className="px-6 py-3">Email</th>
                          <th className="px-6 py-3">Университет</th>
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
                            <td className="px-6 py-4">
                              {new Date(student.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openEditStudentModal(student)}
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

          {/* Заявки */}
          {activeTab === 'requests' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Заявки на услуги</h2>
                <Button onClick={() => setShowCreateRequest(true)}>
                  Создать заявку
                </Button>
              </div>

              {showCreateRequest && (
                <Card>
                  <CardHeader>
                    <CardTitle>Создать новую заявку</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={createServiceRequest} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="student_id">Студент *</Label>
                          <Select 
                            value={requestForm.student_id}
                            onValueChange={(value) => setRequestForm({...requestForm, student_id: value})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Выберите студента" />
                            </SelectTrigger>
                            <SelectContent className="max-h-60 overflow-y-auto">
                              {students.map((student) => (
                                <SelectItem key={student.student_id} value={student.student_id.toString()}>
                                  {student.first_name} {student.last_name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label htmlFor="service_type_id">Тип услуги *</Label>
                          <Select 
                            value={requestForm.service_type_id}
                            onValueChange={(value) => setRequestForm({...requestForm, service_type_id: value})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Выберите услугу" />
                            </SelectTrigger>
                            <SelectContent className="max-h-60 overflow-y-auto w-full min-w-[800px] max-w-[90vw]">
                              {(() => {
                                // Группируем услуги на пакеты и индивидуальные услуги
                                const packages = sortServicesByLandingOrder(
                                  serviceTypes.filter(service => 
                                    service.name.includes('Пакет') || service.name.includes('пакет') ||
                                    service.description.includes('Пакет') || service.description.includes('пакет') ||
                                    service.name.includes('Премиум') || service.description.includes('Премиум')
                                  )
                                )
                                const individualServices = sortServicesByLandingOrder(
                                  serviceTypes.filter(service => 
                                    !service.name.includes('Пакет') && !service.name.includes('пакет') &&
                                    !service.description.includes('Пакет') && !service.description.includes('пакет') &&
                                    !service.name.includes('Премиум') && !service.description.includes('Премиум')
                                  )
                                )

                                return (
                                  <>
                                    {/* Пакеты */}
                                    <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase bg-gray-50">
                                      Пакеты услуг
                                    </div>
                                    {packages.map((service) => (
                                      <SelectItem key={service.service_type_id} value={service.service_type_id.toString()}>
                                        {service.name} - {service.has_custom_price ? 
                                          `£${service.price_gbp || 0} ($${service.price_usd || 0}) | ${Number(service.price_uzs || 0).toLocaleString()} сум (специальная цена)` : 
                                          service.price_text}
                                      </SelectItem>
                                    ))}
                                    
                                    {/* Разделитель */}
                                    {packages.length > 0 && individualServices.length > 0 && (
                                      <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase bg-gray-50 border-t">
                                        Индивидуальные услуги
                                      </div>
                                    )}
                                    
                                    {/* Индивидуальные услуги */}
                                    {individualServices.map((service) => (
                                      <SelectItem key={service.service_type_id} value={service.service_type_id.toString()}>
                                        {service.name} - {service.has_custom_price ? 
                                          `£${service.price_gbp || 0} ($${service.price_usd || 0}) | ${Number(service.price_uzs || 0).toLocaleString()} сум (специальная цена)` : 
                                          service.price_text}
                                      </SelectItem>
                                    ))}
                                  </>
                                )
                              })()}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="md:col-span-2">
                          <Label htmlFor="title">Название заявки *</Label>
                          <Input
                            id="title"
                            value={requestForm.title}
                            onChange={(e) => setRequestForm({...requestForm, title: e.target.value})}
                            required
                          />
                        </div>
                        <div className="md:col-span-2">
                          <Label htmlFor="description">Описание</Label>
                          <Input
                            id="description"
                            value={requestForm.description}
                            onChange={(e) => setRequestForm({...requestForm, description: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="priority">Приоритет</Label>
                          <Select 
                            value={requestForm.priority}
                            onValueChange={(value) => setRequestForm({...requestForm, priority: value})}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="max-h-60 overflow-y-auto">
                              <SelectItem value="low">Низкий</SelectItem>
                              <SelectItem value="medium">Средний</SelectItem>
                              <SelectItem value="high">Высокий</SelectItem>
                              <SelectItem value="urgent">Срочно</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label htmlFor="scheduled_date">Дата выполнения</Label>
                          <Input
                            id="scheduled_date"
                            type="datetime-local"
                            value={requestForm.scheduled_date}
                            onChange={(e) => setRequestForm({...requestForm, scheduled_date: e.target.value})}
                          />
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button type="submit">Создать заявку</Button>
                        <Button type="button" variant="outline" onClick={() => setShowCreateRequest(false)}>
                          Отмена
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>Заявки сгруппированы по студентам</CardTitle>
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
            </div>
          )}

          {/* Цены */}
          {activeTab === 'pricing' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Управление ценами</h2>
              
              {/* Индивидуальные цены на стандартные услуги */}
              <Card>
                <CardHeader>
                  <CardTitle>Ваши индивидуальные цены</CardTitle>
                  <CardDescription>
                    Специальные цены, установленные для вашего агентства
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {agencyPricing.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                          <tr>
                            <th className="px-6 py-3">Услуга</th>
                            <th className="px-6 py-3">Стандартная цена</th>
                            <th className="px-6 py-3">Ваша цена</th>
                            <th className="px-6 py-3">Экономия</th>
                          </tr>
                        </thead>
                        <tbody>
                          {agencyPricing.map((pricing) => (
                            <tr key={pricing.pricing_id} className="bg-white border-b">
                              <td className="px-6 py-4 font-medium text-gray-900">
                                {pricing.name}
                              </td>
                              <td className="px-6 py-4">
                                <div className="text-sm">
                                  <div>£{pricing.base_price_gbp || pricing.base_price}</div>
                                  <div className="text-gray-500">${pricing.base_price_usd || 0}</div>
                                  <div className="text-gray-500">{(pricing.base_price_uzs || 0).toLocaleString()} сум</div>
                                </div>
                              </td>
                              <td className="px-6 py-4 text-green-600 font-semibold">
                                <div className="text-sm">
                                  <div>£{pricing.price_gbp || pricing.custom_price}</div>
                                  <div>${pricing.price_usd || 0}</div>
                                  <div>{(pricing.price_uzs || 0).toLocaleString()} сум</div>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <div className="text-sm">
                                  {(() => {
                                    const baseGbp = pricing.base_price_gbp || pricing.base_price || 0
                                    const yourGbp = pricing.price_gbp || pricing.custom_price || 0
                                    const baseUsd = pricing.base_price_usd || 0
                                    const yourUsd = pricing.price_usd || 0
                                    const baseUzs = pricing.base_price_uzs || 0
                                    const yourUzs = pricing.price_uzs || 0
                                    
                                    const savingsGbp = baseGbp - yourGbp
                                    const savingsUsd = baseUsd - yourUsd
                                    const savingsUzs = baseUzs - yourUzs
                                    
                                    return (
                                      <>
                                        <div className={savingsGbp > 0 ? "text-green-600" : savingsGbp < 0 ? "text-red-600" : "text-gray-600"}>
                                          {savingsGbp > 0 ? "-" : savingsGbp < 0 ? "+" : ""}£{Math.abs(savingsGbp).toFixed(0)}
                                        </div>
                                        <div className={savingsUsd > 0 ? "text-green-600" : savingsUsd < 0 ? "text-red-600" : "text-gray-600"}>
                                          {savingsUsd > 0 ? "-" : savingsUsd < 0 ? "+" : ""}${Math.abs(savingsUsd).toFixed(0)}
                                        </div>
                                        <div className={savingsUzs > 0 ? "text-green-600" : savingsUzs < 0 ? "text-red-600" : "text-gray-600"}>
                                          {savingsUzs > 0 ? "-" : savingsUzs < 0 ? "+" : ""}{Math.abs(savingsUzs).toLocaleString()} сум
                                        </div>
                                      </>
                                    )
                                  })()}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-gray-500">
                      У вас пока нет индивидуальных цен. Все услуги используют стандартные цены.
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Кастомные услуги агентства */}
              <Card>
                <CardHeader>
                  <CardTitle>Ваши специальные услуги</CardTitle>
                  <CardDescription>
                    Уникальные услуги, доступные только для вашего агентства
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {customServices.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                          <tr>
                            <th className="px-6 py-3">Название</th>
                            <th className="px-6 py-3">Описание</th>
                            <th className="px-6 py-3">Цена</th>
                            <th className="px-6 py-3">Дата создания</th>
                          </tr>
                        </thead>
                        <tbody>
                          {customServices.map((service) => (
                            <tr key={service.custom_service_id} className="bg-white border-b">
                              <td className="px-6 py-4 font-medium text-gray-900">
                                {service.service_name}
                              </td>
                              <td className="px-6 py-4">{service.service_description || 'Без описания'}</td>
                              <td className="px-6 py-4 font-semibold text-blue-600">
                                £{service.price}
                              </td>
                              <td className="px-6 py-4">
                                {new Date(service.created_at).toLocaleDateString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-500 mb-4">
                        У вас пока нет специальных услуг
                      </p>
                      <Button variant="outline">
                        Запросить новую услугу
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Информационная карточка */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-blue-600">ℹ️ Информация о ценах</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>• <strong>Индивидуальные цены</strong> — специальные тарифы, согласованные с NotHard для вашего агентства</p>
                    <p>• <strong>Специальные услуги</strong> — уникальные услуги, созданные под потребности вашей компании</p>
                    <p>• Для изменения цен или добавления новых услуг обращайтесь к администратору</p>
                    <p>• Цены указаны в британских фунтах стерлингов (GBP), долларах США (USD) и узбекских сумах (UZS)</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Архив студентов */}
          {activeTab === 'archive' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold">Архив студентов</h2>
                <Button 
                  onClick={fetchArchivedStudents}
                  variant="outline"
                >
                  🔄 Обновить
                </Button>
              </div>
              
              <Card>
                <CardHeader>
                  <CardTitle>Архивированные студенты</CardTitle>
                  <CardDescription>
                    Студенты, которые завершили все свои заявки и были перемещены в архив
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {archivedStudents.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left border">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                          <tr>
                            <th className="px-4 py-3">Имя</th>
                            <th className="px-4 py-3">Email</th>
                            <th className="px-4 py-3">Телефон</th>
                            <th className="px-4 py-3">Университет</th>
                            <th className="px-4 py-3">Дата архивации</th>
                            <th className="px-4 py-3">Действия</th>
                          </tr>
                        </thead>
                        <tbody>
                          {archivedStudents.map((student) => (
                            <tr key={student.student_id} className="border-b hover:bg-gray-50">
                              <td className="px-4 py-3 font-medium">
                                {student.first_name} {student.last_name}
                              </td>
                              <td className="px-4 py-3">{student.student_email || '-'}</td>
                              <td className="px-4 py-3">{student.student_phone || '-'}</td>
                              <td className="px-4 py-3">{student.university || '-'}</td>
                              <td className="px-4 py-3">
                                {student.archived_at ? new Date(student.archived_at).toLocaleDateString() : '-'}
                              </td>
                              <td className="px-4 py-3">
                                <div className="flex space-x-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => viewArchivedStudentRequests(student)}
                                    title="Посмотреть выполненные заявки"
                                  >
                                    👁️ Подробнее
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => unarchiveStudent(student.student_id)}
                                    title="Восстановить студента"
                                  >
                                    📤 Восстановить
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-500 mb-4">
                        📁 В архиве пока нет студентов
                      </p>
                      <p className="text-sm text-gray-400">
                        Студенты будут автоматически архивированы после завершения всех заявок
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Информация об архивации */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-blue-600">ℹ️ Как работает архивация</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>• <strong>Автоматическая архивация:</strong> Студенты архивируются автоматически, когда все их заявки завершены или отменены</p>
                    <p>• <strong>Ручная архивация:</strong> Вы можете архивировать студента вручную через меню "Заявки студента"</p>
                    <p>• <strong>Восстановление:</strong> Архивированного студента можно восстановить в основной список</p>
                    <p>• <strong>Фильтрация:</strong> Архивированные студенты скрыты из основного списка студентов</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
      <Footer />

      {/* Модальное окно редактирования студента */}
      <Dialog open={showEditStudentModal} onOpenChange={setShowEditStudentModal}>
        <DialogContent className="max-w-6xl w-full" style={{ maxWidth: '1152px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              Редактировать студента: {selectedStudent?.first_name} {selectedStudent?.last_name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editFirstName">Имя</Label>
                <Input
                  id="editFirstName"
                  value={editStudentData.first_name}
                  onChange={(e) => setEditStudentData(prev => ({...prev, first_name: e.target.value}))}
                  placeholder="Введите имя"
                />
              </div>
              
              <div>
                <Label htmlFor="editLastName">Фамилия</Label>
                <Input
                  id="editLastName"
                  value={editStudentData.last_name}
                  onChange={(e) => setEditStudentData(prev => ({...prev, last_name: e.target.value}))}
                  placeholder="Введите фамилию"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editEmail">Email</Label>
                <Input
                  id="editEmail"
                  type="email"
                  value={editStudentData.email}
                  onChange={(e) => setEditStudentData(prev => ({...prev, email: e.target.value}))}
                  placeholder="Введите email"
                />
              </div>
              
              <div>
                <Label htmlFor="editPhone">Телефон</Label>
                <Input
                  id="editPhone"
                  value={editStudentData.phone}
                  onChange={(e) => setEditStudentData(prev => ({...prev, phone: e.target.value}))}
                  placeholder="Введите телефон"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editBirthDate">Дата рождения</Label>
                <Input
                  id="editBirthDate"
                  type="date"
                  value={editStudentData.date_of_birth}
                  onChange={(e) => setEditStudentData(prev => ({...prev, date_of_birth: e.target.value}))}
                />
              </div>
              
              <div>
                <Label htmlFor="editNationality">Гражданство</Label>
                <Input
                  id="editNationality"
                  value={editStudentData.nationality}
                  onChange={(e) => setEditStudentData(prev => ({...prev, nationality: e.target.value}))}
                  placeholder="Введите гражданство"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="editUniversity">Университет</Label>
              <Input
                id="editUniversity"
                value={editStudentData.university}
                onChange={(e) => setEditStudentData(prev => ({...prev, university: e.target.value}))}
                placeholder="Введите университет"
              />
            </div>
            
            <div className="flex justify-between">
              <Button 
                variant="destructive" 
                onClick={() => {
                  if (selectedStudent) {
                    deleteStudent(selectedStudent)
                    setShowEditStudentModal(false)
                  }
                }}
              >
                Удалить студента
              </Button>
              <div className="flex space-x-2">
                <Button variant="outline" onClick={() => setShowEditStudentModal(false)}>
                  Отмена
                </Button>
                <Button onClick={updateStudent}>
                  Сохранить изменения
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно просмотра заявок студента */}
      <Dialog open={showRequestsModal} onOpenChange={setShowRequestsModal}>
        <DialogContent className="max-w-6xl w-full" style={{ maxWidth: '1152px', width: '95vw' }}>
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
                    <th className="px-4 py-3">Оплата</th>
                    <th className="px-4 py-3">Приоритет</th>
                    <th className="px-4 py-3">Раннер</th>
                    <th className="px-4 py-3">Дата создания</th>
                    <th className="px-4 py-3">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {studentServiceRequests.map((request) => {
                    const tasks = requestTasks[request.request_id] || []
                    const isExpanded = expandedRequests[request.request_id]
                    
                    return (
                      <>
                        <tr key={request.request_id} className="border-b hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div>
                              <div className="flex items-center justify-between">
                                <div className="font-medium">{request.title}</div>
                                {tasks.length > 0 && (
                                  <Button
                                    size="sm"
                                    variant={isExpanded ? "secondary" : "outline"}
                                    onClick={() => setExpandedRequests(prev => ({
                                      ...prev,
                                      [request.request_id]: !prev[request.request_id]
                                    }))}
                                    className="ml-2 px-3 py-1 text-xs font-medium transition-all duration-200 hover:shadow-md"
                                    title={isExpanded ? "Скрыть задачи" : "Показать задачи пакета"}
                                  >
                                    {isExpanded ? (
                                      <>
                                        <span className="mr-1">📋</span>
                                        Свернуть
                                        <span className="ml-1">▲</span>
                                      </>
                                    ) : (
                                      <>
                                        <span className="mr-1">📋</span>
                                        Задачи ({tasks.length})
                                        <span className="ml-1">▼</span>
                                      </>
                                    )}
                                  </Button>
                                )}
                              </div>
                              {request.service_description && (
                                <div className="text-xs text-gray-500 mt-1">
                                  {request.service_description}
                                </div>
                              )}
                              {request.description && (
                                <div className="text-xs text-gray-600 mt-1">
                                  {request.description}
                                </div>
                              )}
                              {tasks.length > 0 && (
                                <div className="text-xs text-blue-600 mt-1">
                                  Задач: {tasks.length} (выполнено: {tasks.filter(t => t.status === 'completed').length})
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">{getStatusBadge(request.status)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <Select
                              value={request.payment_status || 'unpaid'}
                              onValueChange={(value) => updatePaymentStatus(request.request_id, value)}
                            >
                              <SelectTrigger className="w-32 min-w-fit">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="unpaid">
                                  <span className="flex items-center">
                                    <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                                    Не оплачено
                                  </span>
                                </SelectItem>
                                <SelectItem value="partial">
                                  <span className="flex items-center">
                                    <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                                    Частично
                                  </span>
                                </SelectItem>
                                <SelectItem value="paid">
                                  <span className="flex items-center">
                                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                                    Оплачено
                                  </span>
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">{getPriorityBadge(request.priority)}</td>
                          <td className="px-4 py-3 whitespace-nowrap">{request.runner_name || 'Не назначен'}</td>
                          <td className="px-4 py-3">
                            <div className="text-sm">
                              {new Date(request.created_at).toLocaleDateString()}
                            </div>
                            {request.scheduled_date && (
                              <div className="text-xs text-gray-500">
                                Запланировано: {new Date(request.scheduled_date).toLocaleDateString()}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => openEditRequestModal(request)}
                              >
                                Редактировать
                              </Button>
                              {request.status !== 'completed' && request.status !== 'cancelled' && (
                                <Button
                                  size="sm"
                                  variant="default"
                                  onClick={() => completeRequestManually(request.request_id)}
                                >
                                  Завершить
                                </Button>
                              )}
                              {request.status === 'completed' && (
                                <Button
                                  size="sm"
                                  variant="secondary"
                                  onClick={() => uncompleteRequest(request.request_id)}
                                >
                                  ↻ Отменить завершение
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={async () => {
                                  const success = await deleteRequest(request.request_id)
                                  if (success) {
                                    // Перезагружаем заявки студента
                                    if (selectedRequestStudent) {
                                      try {
                                        const response = await fetch(`${apiUrl}/api/service-requests?student_id=${selectedRequestStudent.student_id}`)
                                        if (response.ok) {
                                          const data = await response.json()
                                          setStudentServiceRequests(data.requests || [])
                                        }
                                      } catch (error) {
                                        console.error('Ошибка при перезагрузке заявок:', error)
                                      }
                                    }
                                  }
                                }}
                              >
                                Удалить
                              </Button>
                            </div>
                          </td>
                        </tr>
                        
                        {/* Развернутые задачи */}
                        {isExpanded && tasks.length > 0 && (
                          <tr key={`tasks-${request.request_id}`} className="bg-gray-50">
                            <td colSpan={6} className="px-4 py-3">
                              <div className="ml-4">
                                <h4 className="font-medium mb-2 text-gray-700">Задачи заявки:</h4>
                                <div className="space-y-2">
                                  {tasks.map((task) => {
                                    const isHousingTask = task.service_name && (
                                      task.service_name.includes('жилье') || 
                                      task.service_name.includes('Жилье') ||
                                      task.service_name.includes('подбор')
                                    )
                                    const properties = taskProperties[task.task_id] || []
                                    
                                    return (
                                      <div key={task.task_id} className="p-3 bg-white rounded border space-y-3">
                                        <div className="flex items-center justify-between">
                                          <div className="flex-1">
                                            <div className="font-medium text-sm">{task.service_name}</div>
                                            <div className="text-xs text-gray-500">
                                              Создано: {new Date(task.created_at).toLocaleDateString()}
                                              {task.updated_at && task.updated_at !== task.created_at && (
                                                <span> • Обновлено: {new Date(task.updated_at).toLocaleDateString()}</span>
                                              )}
                                            </div>
                                          </div>
                                          <div className="flex items-center space-x-2">
                                            <Select 
                                              value={task.status} 
                                              onValueChange={(value) => updateTaskStatus(task.task_id, value, request.request_id)}
                                            >
                                              <SelectTrigger className="w-32">
                                                <SelectValue />
                                              </SelectTrigger>
                                              <SelectContent>
                                                <SelectItem value="waiting">Ожидание</SelectItem>
                                                <SelectItem value="in_progress">В процессе</SelectItem>
                                                <SelectItem value="completed">Выполнено</SelectItem>
                                                <SelectItem value="cancelled">Отменено</SelectItem>
                                              </SelectContent>
                                            </Select>
                                            <Badge variant={
                                              task.status === 'completed' ? 'default' :
                                              task.status === 'in_progress' ? 'secondary' :
                                              task.status === 'cancelled' ? 'destructive' : 'outline'
                                            }>
                                              {
                                                task.status === 'waiting' ? 'Ожидание' :
                                                task.status === 'in_progress' ? 'В процессе' :
                                                task.status === 'completed' ? 'Выполнено' :
                                                task.status === 'cancelled' ? 'Отменено' : task.status
                                              }
                                            </Badge>
                                          </div>
                                        </div>
                                        
                                        {/* Управление недвижимостью для жилищных задач */}
                                        {isHousingTask && (
                                          <div className="border-t pt-3 space-y-3">
                                            <div className="flex items-center justify-between">
                                              <h5 className="font-medium text-sm text-gray-700">
                                                🏠 Недвижимость ({properties.length})
                                              </h5>
                                              <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => {
                                                  setSelectedTaskForProperty(task.task_id)
                                                  setShowAddPropertyModal(true)
                                                }}
                                              >
                                                + Добавить объект
                                              </Button>
                                            </div>
                                            
                                            {properties.length > 0 && (
                                              <div className="space-y-2 max-h-60 overflow-y-auto">
                                                {properties.map((property) => (
                                                  <div key={property.property_id} className="p-2 bg-gray-50 rounded text-xs">
                                                    <div className="flex items-start justify-between mb-1">
                                                      <div className="flex-1 mr-2">
                                                        <div className="font-medium text-blue-600">
                                                          <a href={property.property_url} target="_blank" rel="noopener noreferrer">
                                                            {property.property_title || 'Объект недвижимости'}
                                                          </a>
                                                        </div>
                                                        {property.property_address && (
                                                          <div className="text-gray-600">{property.property_address}</div>
                                                        )}
                                                        {property.property_rent && (
                                                          <div className="text-green-600 font-medium">{property.property_rent}</div>
                                                        )}
                                                      </div>
                                                      <div className="flex items-center space-x-1">
                                                        <Select
                                                          value={property.status}
                                                          onValueChange={(value) => updatePropertyStatus(property.property_id, value, task.task_id)}
                                                        >
                                                          <SelectTrigger className="w-20 h-6 text-xs">
                                                            <SelectValue />
                                                          </SelectTrigger>
                                                          <SelectContent>
                                                            <SelectItem value="pending">Ожидание</SelectItem>
                                                            <SelectItem value="contacted">Связались</SelectItem>
                                                            <SelectItem value="available">Доступна</SelectItem>
                                                            <SelectItem value="unavailable">Недоступна</SelectItem>
                                                            <SelectItem value="viewing_scheduled">Просмотр назначен</SelectItem>
                                                            <SelectItem value="viewing_completed">Просмотр проведен</SelectItem>
                                                            <SelectItem value="selected">Выбрана</SelectItem>
                                                            <SelectItem value="rejected">Отклонена</SelectItem>
                                                          </SelectContent>
                                                        </Select>
                                                        <Button
                                                          size="sm"
                                                          variant="outline"
                                                          onClick={() => openEditPropertyModal(property)}
                                                          className="h-6 px-2 text-xs mr-1"
                                                        >
                                                          ✏️ Редактировать
                                                        </Button>
                                                        <Button
                                                          size="sm"
                                                          variant={property.is_selected_for_viewing ? "default" : "outline"}
                                                          onClick={() => selectPropertyForViewing(
                                                            property.property_id, 
                                                            !property.is_selected_for_viewing,
                                                            task.task_id
                                                          )}
                                                          className="h-6 px-2 text-xs"
                                                        >
                                                          {property.is_selected_for_viewing ? '✓ Выбрана' : 'Выбрать'}
                                                        </Button>
                                                      </div>
                                                    </div>
                                                    {property.property_description && (
                                                      <div className="text-gray-500 text-xs mt-1">
                                                        {property.property_description.substring(0, 100)}...
                                                      </div>
                                                    )}
                                                    {property.agent_notes && (
                                                      <div className="text-blue-600 text-xs mt-1 font-medium">
                                                        💬 {property.agent_notes}
                                                      </div>
                                                    )}
                                                  </div>
                                                ))}
                                              </div>
                                            )}
                                            
                                            {properties.length === 0 && (
                                              <div className="text-center text-gray-500 text-xs py-2">
                                                Нет добавленных объектов недвижимости
                                              </div>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    )
                                  })}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    )
                  })}
                </tbody>
              </table>
            </div>
            
            <div className="flex justify-between">
              <Button 
                variant="secondary" 
                onClick={() => selectedRequestStudent && archiveStudent(selectedRequestStudent.student_id)}
                className="bg-yellow-600 hover:bg-yellow-700 text-white"
              >
                📁 Архивировать студента
              </Button>
              <Button variant="outline" onClick={() => setShowRequestsModal(false)}>
                Закрыть
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно редактирования заявки */}
      <Dialog open={showEditRequestModal} onOpenChange={setShowEditRequestModal}>
        <DialogContent className="max-w-6xl w-full" style={{ maxWidth: '1152px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              Редактировать заявку: {selectedRequest?.title}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editTitle">Название заявки</Label>
                <Input
                  id="editTitle"
                  value={editRequestData.title}
                  onChange={(e) => setEditRequestData(prev => ({...prev, title: e.target.value}))}
                  placeholder="Введите название"
                />
              </div>
              
              <div>
                <Label htmlFor="editStatus">Статус</Label>
                <select
                  id="editStatus"
                  value={editRequestData.status}
                  onChange={(e) => setEditRequestData(prev => ({...prev, status: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="new">Новая</option>
                  <option value="assigned">Назначена</option>
                  <option value="in_progress">Выполняется</option>
                  <option value="completed">Завершена</option>
                  <option value="cancelled">Отменена</option>
                </select>
              </div>
              
              <div>
                <Label htmlFor="editPriority">Приоритет</Label>
                <select
                  id="editPriority"
                  value={editRequestData.priority}
                  onChange={(e) => setEditRequestData(prev => ({...prev, priority: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="low">Низкий</option>
                  <option value="medium">Средний</option>
                  <option value="high">Высокий</option>
                  <option value="urgent">Срочно</option>
                </select>
              </div>
              
              <div>
                <Label htmlFor="editPrice">Цена</Label>
                <Input
                  id="editPrice"
                  type="number"
                  step="0.01"
                  value={editRequestData.price}
                  onChange={(e) => setEditRequestData(prev => ({...prev, price: e.target.value}))}
                  placeholder="Введите цену"
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="editDescription">Описание</Label>
              <textarea
                id="editDescription"
                value={editRequestData.description}
                onChange={(e) => setEditRequestData(prev => ({...prev, description: e.target.value}))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={3}
                placeholder="Введите описание"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="editLocation">Место</Label>
                <Input
                  id="editLocation"
                  value={editRequestData.location}
                  onChange={(e) => setEditRequestData(prev => ({...prev, location: e.target.value}))}
                  placeholder="Введите место"
                />
              </div>
              
              <div>
                <Label htmlFor="editScheduledDate">Запланированная дата</Label>
                <Input
                  id="editScheduledDate"
                  type="datetime-local"
                  value={editRequestData.scheduled_date}
                  onChange={(e) => setEditRequestData(prev => ({...prev, scheduled_date: e.target.value}))}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="editNotes">Заметки</Label>
              <textarea
                id="editNotes"
                value={editRequestData.notes}
                onChange={(e) => setEditRequestData(prev => ({...prev, notes: e.target.value}))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={2}
                placeholder="Введите заметки"
              />
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowEditRequestModal(false)}>
                Отмена
              </Button>
              <Button onClick={updateRequest}>
                Сохранить изменения
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модал для добавления недвижимости */}
      <Dialog open={showAddPropertyModal} onOpenChange={setShowAddPropertyModal}>
        <DialogContent className="max-w-4xl" style={{ maxWidth: '800px', width: '90vw' }}>
          <div>
            <h3 className="text-lg font-semibold mb-4">Добавить объект недвижимости</h3>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="propertyUrl">URL объекта *</Label>
                <Input
                  id="propertyUrl"
                  placeholder="https://example.com/property"
                  value={newProperty.property_url}
                  onChange={(e) => setNewProperty(prev => ({...prev, property_url: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="propertyTitle">Название объекта</Label>
                <Input
                  id="propertyTitle"
                  placeholder="Например: 2-комнатная квартира в центре"
                  value={newProperty.property_title}
                  onChange={(e) => setNewProperty(prev => ({...prev, property_title: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="propertyAddress">Адрес</Label>
                <Input
                  id="propertyAddress"
                  placeholder="Например: 123 Main Street, London"
                  value={newProperty.property_address}
                  onChange={(e) => setNewProperty(prev => ({...prev, property_address: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="propertyRent">Цена аренды</Label>
                <Input
                  id="propertyRent"
                  placeholder="Например: £1500/месяц"
                  value={newProperty.property_rent}
                  onChange={(e) => setNewProperty(prev => ({...prev, property_rent: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="propertyDescription">Описание</Label>
                <textarea
                  id="propertyDescription"
                  rows={3}
                  placeholder="Описание объекта недвижимости..."
                  value={newProperty.property_description}
                  onChange={(e) => setNewProperty(prev => ({...prev, property_description: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 mt-6">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowAddPropertyModal(false)
                  setSelectedTaskForProperty(null)
                  setNewProperty({
                    property_url: '',
                    property_title: '',
                    property_address: '',
                    property_rent: '',
                    property_description: ''
                  })
                }}
              >
                Отмена
              </Button>
              <Button onClick={() => selectedTaskForProperty && addProperty(selectedTaskForProperty)}>
                Добавить объект
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модал для редактирования недвижимости */}
      <Dialog open={showEditPropertyModal} onOpenChange={setShowEditPropertyModal}>
        <DialogContent className="max-w-4xl" style={{ maxWidth: '800px', width: '90vw' }}>
          <div>
            <h3 className="text-lg font-semibold mb-4">Редактировать объект недвижимости</h3>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="editPropertyUrl">URL объекта *</Label>
                <Input
                  id="editPropertyUrl"
                  placeholder="https://example.com/property"
                  value={editProperty.property_url}
                  onChange={(e) => setEditProperty(prev => ({...prev, property_url: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="editPropertyTitle">Название объекта</Label>
                <Input
                  id="editPropertyTitle"
                  placeholder="Например: 2-комнатная квартира в центре"
                  value={editProperty.property_title}
                  onChange={(e) => setEditProperty(prev => ({...prev, property_title: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="editPropertyAddress">Адрес</Label>
                <Input
                  id="editPropertyAddress"
                  placeholder="Например: 123 Main Street, London"
                  value={editProperty.property_address}
                  onChange={(e) => setEditProperty(prev => ({...prev, property_address: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="editPropertyRent">Арендная плата</Label>
                <Input
                  id="editPropertyRent"
                  placeholder="Например: £1500/месяц"
                  value={editProperty.property_rent}
                  onChange={(e) => setEditProperty(prev => ({...prev, property_rent: e.target.value}))}
                  className="w-full"
                />
              </div>
              
              <div>
                <Label htmlFor="editPropertyDescription">Описание</Label>
                <textarea
                  id="editPropertyDescription"
                  placeholder="Дополнительная информация об объекте"
                  value={editProperty.property_description}
                  onChange={(e) => setEditProperty(prev => ({...prev, property_description: e.target.value}))}
                  className="w-full min-h-[80px] px-3 py-2 text-sm rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <Label htmlFor="editAgentNotes">Комментарии агента</Label>
                <textarea
                  id="editAgentNotes"
                  placeholder="Ваши заметки об этом объекте (только для агентов)"
                  value={editProperty.agent_notes}
                  onChange={(e) => setEditProperty(prev => ({...prev, agent_notes: e.target.value}))}
                  className="w-full min-h-[60px] px-3 py-2 text-sm rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="text-xs text-gray-500 mt-1">
                  💬 Приватные заметки: "Хорошая локация", "Слишком дорого", "Обратить внимание на состояние" и т.д.
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowEditPropertyModal(false)
                    setSelectedPropertyForEdit(null)
                  }}
                >
                  Отмена
                </Button>
                <Button
                  onClick={updateProperty}
                >
                  Сохранить изменения
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно просмотра заявок архивированного студента */}
      <Dialog open={showArchivedStudentModal} onOpenChange={setShowArchivedStudentModal}>
        <DialogContent className="max-w-6xl w-full" style={{ maxWidth: '1152px', width: '95vw' }}>
          <DialogHeader>
            <DialogTitle>
              История заявок: {selectedArchivedStudent?.first_name} {selectedArchivedStudent?.last_name}
              <Badge variant="secondary" className="ml-2">Архивирован</Badge>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p><strong>Email:</strong> {selectedArchivedStudent?.student_email || selectedArchivedStudent?.email || 'Не указан'}</p>
              </div>
              <div>
                <p><strong>Телефон:</strong> {selectedArchivedStudent?.student_phone || selectedArchivedStudent?.phone || 'Не указан'}</p>
              </div>
              <div>
                <p><strong>Дата архивации:</strong> {selectedArchivedStudent?.archived_at ? new Date(selectedArchivedStudent.archived_at).toLocaleDateString() : '-'}</p>
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
                    <th className="px-4 py-3">Цена</th>
                  </tr>
                </thead>
                <tbody>
                  {archivedStudentRequests.length > 0 ? (
                    archivedStudentRequests.map((request) => (
                      <tr key={request.request_id} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div>
                            <div className="font-medium">{request.title}</div>
                            {request.service_description && (
                              <div className="text-xs text-gray-500 mt-1">
                                {request.service_description}
                              </div>
                            )}
                            {request.description && (
                              <div className="text-xs text-gray-600 mt-1">
                                {request.description}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">{getStatusBadge(request.status)}</td>
                        <td className="px-4 py-3">{getPriorityBadge(request.priority)}</td>
                        <td className="px-4 py-3">{request.runner_name || 'Не назначен'}</td>
                        <td className="px-4 py-3">
                          <div className="text-sm">
                            {new Date(request.created_at).toLocaleDateString()}
                          </div>
                          {request.scheduled_date && (
                            <div className="text-xs text-gray-500">
                              Запланировано: {new Date(request.scheduled_date).toLocaleDateString()}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {request.price ? `£${request.price}` : '-'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                        У этого студента нет заявок
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">📊 Статистика выполнения</h4>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-blue-600 font-semibold">
                    {archivedStudentRequests.filter(r => r.status === 'completed').length}
                  </div>
                  <div className="text-gray-600">Завершено</div>
                </div>
                <div>
                  <div className="text-red-600 font-semibold">
                    {archivedStudentRequests.filter(r => r.status === 'cancelled').length}
                  </div>
                  <div className="text-gray-600">Отменено</div>
                </div>
                <div>
                  <div className="text-yellow-600 font-semibold">
                    {archivedStudentRequests.filter(r => r.status === 'in_progress').length}
                  </div>
                  <div className="text-gray-600">В процессе</div>
                </div>
                <div>
                  <div className="text-gray-600 font-semibold">
                    {archivedStudentRequests.length}
                  </div>
                  <div className="text-gray-600">Всего заявок</div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between">
              <Button 
                variant="secondary" 
                onClick={() => selectedArchivedStudent && unarchiveStudent(selectedArchivedStudent.student_id)}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                📤 Восстановить студента
              </Button>
              <Button variant="outline" onClick={() => setShowArchivedStudentModal(false)}>
                Закрыть
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
