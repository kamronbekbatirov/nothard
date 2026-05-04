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

interface ServiceRequest {
  request_id: number
  student_id: number
  first_name: string
  last_name: string
  student_email: string
  service_name: string
  title: string
  description?: string
  status: string
  priority: string
  price: number
  scheduled_date?: string
  location?: string
  notes?: string
  agency_name?: string
  created_at: string
}

export default function RunnerPanel() {
  const [user, setUser] = useState<any>(null)
  const [serviceRequests, setServiceRequests] = useState<ServiceRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('available')
  const [selectedRequest, setSelectedRequest] = useState<ServiceRequest | null>(null)
  const [statusComment, setStatusComment] = useState('')
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

    if (!userRole || userRole !== 'runner') {
      toast({
        title: "Доступ запрещен",
        description: "У вас нет прав раннера",
        variant: "destructive",
      })
      router.push('/login')
      return
    }

    setUser({ role: userRole, id: userId, name: userName })
    fetchData(userId || '1')
  }

  const fetchData = async (userId: string) => {
    try {
      setLoading(true)
      
      // Получаем заявки для раннера
      const response = await fetch(`${apiUrl}/api/service-requests?user_role=runner&runner_id=${userId}`)
      if (response.ok) {
        const data = await response.json()
        setServiceRequests(data.requests || [])
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

  const updateRequestStatus = async (requestId: number, newStatus: string, comment: string = '') => {
    try {
      const response = await fetch(`${apiUrl}/api/service-requests/${requestId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status: newStatus,
          changed_by: user.id,
          comment: comment || `Статус изменен раннером на: ${newStatus}`
        }),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Статус заявки обновлен",
        })
        fetchData(user.id) // Обновляем данные
        setSelectedRequest(null)
        setStatusComment('')
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

  const takeRequest = async (requestId: number) => {
    try {
      const response = await fetch(`${apiUrl}/api/assign-runner`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request_id: requestId,
          runner_id: user.id,
          assigned_by: user.id
        }),
      })

      if (response.ok) {
        toast({
          title: "Успешно",
          description: "Вы назначены на выполнение заявки",
        })
        fetchData(user.id) // Обновляем данные
      } else {
        throw new Error('Failed to take request')
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Не удалось взять заявку в работу",
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
      'urgent': { label: 'СРОЧНО!', variant: 'destructive' }
    }
    
    const priorityInfo = priorityMap[priority] || { label: priority, variant: 'default' }
    return <Badge variant={priorityInfo.variant}>{priorityInfo.label}</Badge>
  }

  const availableRequests = serviceRequests.filter(r => r.status === 'new')
  const myRequests = serviceRequests.filter(r => r.status !== 'new')

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
            <h1 className="text-3xl font-bold text-gray-900">Панель раннера</h1>
            <p className="text-gray-600 mt-2">Добро пожаловать, {user?.name}</p>
          </div>

          {/* Навигация по вкладкам */}
          <div className="flex space-x-1 mb-6">
            {[
              { id: 'available', label: `Доступные (${availableRequests.length})` },
              { id: 'my-tasks', label: `Мои задания (${myRequests.length})` },
              { id: 'completed', label: 'Завершенные' }
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

          {/* Обзорные карточки */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader>
                <CardTitle>Доступных заданий</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">{availableRequests.length}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Мои активные</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">
                  {myRequests.filter(r => ['assigned', 'in_progress'].includes(r.status)).length}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Завершено сегодня</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">
                  {myRequests.filter(r => r.status === 'completed' && 
                    new Date(r.created_at).toDateString() === new Date().toDateString()).length}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Срочных заданий</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-red-600">
                  {availableRequests.filter(r => r.priority === 'urgent').length}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Доступные задания */}
          {activeTab === 'available' && (
            <Card>
              <CardHeader>
                <CardTitle>Доступные задания</CardTitle>
                <CardDescription>Выберите задание для выполнения</CardDescription>
              </CardHeader>
              <CardContent>
                {availableRequests.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Нет доступных заданий</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {availableRequests.map((request) => (
                      <div key={request.request_id} className="border rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-semibold text-lg">{request.title}</h3>
                            <p className="text-sm text-gray-600">
                              Студент: {request.first_name} {request.last_name}
                            </p>
                            <p className="text-sm text-gray-600">
                              Агентство: {request.agency_name || 'Прямое обращение'}
                            </p>
                          </div>
                          <div className="text-right">
                            {getPriorityBadge(request.priority)}
                            <div className="mt-2 text-lg font-bold text-green-600">
                              £{request.price}
                            </div>
                          </div>
                        </div>
                        
                        {request.description && (
                          <p className="text-sm text-gray-700 mb-2">{request.description}</p>
                        )}
                        
                        {request.location && (
                          <p className="text-sm text-gray-600 mb-2">
                            <span className="font-medium">Место:</span> {request.location}
                          </p>
                        )}
                        
                        {request.scheduled_date && (
                          <p className="text-sm text-gray-600 mb-2">
                            <span className="font-medium">Дата:</span> {' '}
                            {new Date(request.scheduled_date).toLocaleString()}
                          </p>
                        )}
                        
                        <div className="flex justify-between items-center mt-4">
                          <p className="text-xs text-gray-500">
                            Создано: {new Date(request.created_at).toLocaleString()}
                          </p>
                          <Button onClick={() => takeRequest(request.request_id)}>
                            Взять в работу
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Мои задания */}
          {activeTab === 'my-tasks' && (
            <Card>
              <CardHeader>
                <CardTitle>Мои задания</CardTitle>
                <CardDescription>Управление назначенными вам заданиями</CardDescription>
              </CardHeader>
              <CardContent>
                {myRequests.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">У вас нет назначенных заданий</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {myRequests.filter(r => r.status !== 'completed').map((request) => (
                      <div key={request.request_id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-semibold text-lg">{request.title}</h3>
                            <p className="text-sm text-gray-600">
                              Студент: {request.first_name} {request.last_name}
                            </p>
                            <p className="text-sm text-gray-600">
                              Email: {request.student_email}
                            </p>
                          </div>
                          <div className="text-right">
                            {getStatusBadge(request.status)}
                            {getPriorityBadge(request.priority)}
                            <div className="mt-2 text-lg font-bold text-green-600">
                              £{request.price}
                            </div>
                          </div>
                        </div>
                        
                        {request.description && (
                          <p className="text-sm text-gray-700 mb-2">{request.description}</p>
                        )}
                        
                        {request.location && (
                          <p className="text-sm text-gray-600 mb-2">
                            <span className="font-medium">Место:</span> {request.location}
                          </p>
                        )}
                        
                        {request.scheduled_date && (
                          <p className="text-sm text-gray-600 mb-2">
                            <span className="font-medium">Дата:</span> {' '}
                            {new Date(request.scheduled_date).toLocaleString()}
                          </p>
                        )}
                        
                        <div className="flex justify-between items-center mt-4">
                          <p className="text-xs text-gray-500">
                            Создано: {new Date(request.created_at).toLocaleString()}
                          </p>
                          <div className="space-x-2">
                            {request.status === 'assigned' && (
                              <Button 
                                onClick={() => updateRequestStatus(request.request_id, 'in_progress')}
                                variant="outline"
                              >
                                Начать выполнение
                              </Button>
                            )}
                            {request.status === 'in_progress' && (
                              <Button 
                                onClick={() => setSelectedRequest(request)}
                                className="bg-green-600 hover:bg-green-700"
                              >
                                Завершить
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Завершенные задания */}
          {activeTab === 'completed' && (
            <Card>
              <CardHeader>
                <CardTitle>Завершенные задания</CardTitle>
                <CardDescription>История выполненных заданий</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                      <tr>
                        <th className="px-6 py-3">Студент</th>
                        <th className="px-6 py-3">Услуга</th>
                        <th className="px-6 py-3">Сумма</th>
                        <th className="px-6 py-3">Дата завершения</th>
                      </tr>
                    </thead>
                    <tbody>
                      {myRequests.filter(r => r.status === 'completed').map((request) => (
                        <tr key={request.request_id} className="bg-white border-b hover:bg-gray-50">
                          <td className="px-6 py-4 font-medium text-gray-900">
                            {request.first_name} {request.last_name}
                          </td>
                          <td className="px-6 py-4">{request.title}</td>
                          <td className="px-6 py-4 text-green-600 font-semibold">
                            £{request.price}
                          </td>
                          <td className="px-6 py-4">
                            {new Date(request.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Модальное окно для завершения задания */}
          {selectedRequest && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <Card className="w-[500px] max-w-[90vw]">
                <CardHeader>
                  <CardTitle>Завершить задание</CardTitle>
                  <CardDescription>
                    {selectedRequest.title} - {selectedRequest.first_name} {selectedRequest.last_name}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="comment">Комментарий к выполнению (необязательно)</Label>
                    <Input
                      id="comment"
                      value={statusComment}
                      onChange={(e) => setStatusComment(e.target.value)}
                      placeholder="Опишите детали выполнения задания"
                    />
                  </div>
                  <div className="flex space-x-2">
                    <Button 
                      onClick={() => updateRequestStatus(selectedRequest.request_id, 'completed', statusComment)}
                      className="flex-1"
                    >
                      Завершить задание
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => setSelectedRequest(null)}
                      className="flex-1"
                    >
                      Отмена
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  )
}
