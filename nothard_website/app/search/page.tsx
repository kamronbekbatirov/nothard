'use client';

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Heart, Eye, Search } from 'lucide-react'
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Checkbox } from "../components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "../components/ui/card"
import { Navbar } from "../components/navbar"
import { Footer } from "../components/footer"

interface Property {
  ad_link: string;
  address: string;
  price: string;
  pw_price: string;
  description: string;
  property_type: string;
  bedrooms: string;
  bathrooms: string;
  photo_links: string;
  agency_logo: string;
  agency_phone: string;
  reduced_info?: string;
}

const propertyTypeEmoji: { [key: string]: string } = {
  'Flat': '🏢',
  'Apartment': '🏢',
  'Studio': '🏠',
  'Detached': '🏡',
  'Semi-Detached': '🏘️',
  'Terraced': '🏘️',
  'Maisonette': '🏠',
  'Bungalow': '🏡',
  'Cottage': '🏡',
  'House': '🏠',
}

const getPropertyEmoji = (type: string): string => {
  const normalizedType = type.toLowerCase()
  for (const [key, emoji] of Object.entries(propertyTypeEmoji)) {
    if (normalizedType.includes(key.toLowerCase())) {
      return emoji
    }
  }
  return '🏠'
}

function SearchContent() {
  const [properties, setProperties] = useState<Property[]>([])
  const [filteredProperties, setFilteredProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [minBudget, setMinBudget] = useState('min')
  const [maxBudget, setMaxBudget] = useState('max')
  const [minRooms, setMinRooms] = useState('min')
  const [maxRooms, setMaxRooms] = useState('max')
  const [selectedZones, setSelectedZones] = useState<string[]>([])
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [selectedFurnishing, setSelectedFurnishing] = useState<string[]>([])

  const searchParams = useSearchParams()

  const budgetOptions = [
    '100', '150', '200', '250', '300', '350', '400', '450', '500', '600', '700', '800', '900',
    '1000', '1100', '1200', '1250', '1300', '1400', '1500', '1750', '2000', '2250', '2500',
    '2750', '3000', '3500', '4000', '4500', '5000', '5500', '6000', '6500', '7000', '8000',
    '9000', '10000', '12500', '15000', '17500', '20000', '25000', '30000', '35000', '40000'
  ]
  const minRoomOptions = ['min', 'Studio', ...Array.from({length: 10}, (_, i) => `${i + 1} комнатная`)]
  const maxRoomOptions = ['max', 'Studio', ...Array.from({length: 10}, (_, i) => `${i + 1} комнатная`)]

  useEffect(() => {
    // Get initial filter values from URL parameters
    const minBudgetParam = searchParams.get('minBudget') || 'min'
    const maxBudgetParam = searchParams.get('maxBudget') || 'max'
    const minRoomsParam = searchParams.get('minRooms') || 'min'
    const maxRoomsParam = searchParams.get('maxRooms') || 'max'
    const zonesParam = searchParams.get('zones')?.split(',') || []
    const typesParam = searchParams.get('types')?.split(',') || []

    setMinBudget(minBudgetParam)
    setMaxBudget(maxBudgetParam)
    setMinRooms(minRoomsParam)
    setMaxRooms(maxRoomsParam)
    setSelectedZones(zonesParam)
    setSelectedTypes(typesParam)

    // Load properties
    const fetchProperties = async () => {
      try {
        const response = await fetch('/scraped_properties.json')
        if (!response.ok) {
          throw new Error('Failed to load properties')
        }
        const data = await response.json()
        setProperties(data)
        filterProperties(data, {
          minBudget: minBudgetParam,
          maxBudget: maxBudgetParam,
          minRooms: minRoomsParam,
          maxRooms: maxRoomsParam,
          zones: zonesParam,
          types: typesParam
        })
      } catch (error) {
        console.error('Error loading properties:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchProperties()
  }, [searchParams])

  const filterProperties = (props: Property[], filters: any) => {
    let filtered = [...props]

    // Filter by price
    if (filters.minBudget !== 'min') {
      filtered = filtered.filter(p => {
        const price = parseInt(p.price.replace(/[^0-9]/g, ''))
        return price >= parseInt(filters.minBudget)
      })
    }
    if (filters.maxBudget !== 'max') {
      filtered = filtered.filter(p => {
        const price = parseInt(p.price.replace(/[^0-9]/g, ''))
        return price <= parseInt(filters.maxBudget)
      })
    }

    // Filter by rooms
    if (filters.minRooms !== 'min' && filters.minRooms !== 'Studio') {
      const minRoomsNum = parseInt(filters.minRooms)
      filtered = filtered.filter(p => {
        if (p.bedrooms === '0' || p.property_type === 'Studio') return false
        return parseInt(p.bedrooms) >= minRoomsNum
      })
    }
    if (filters.maxRooms !== 'max' && filters.maxRooms !== 'Studio') {
      const maxRoomsNum = parseInt(filters.maxRooms)
      filtered = filtered.filter(p => {
        if (p.bedrooms === '0' || p.property_type === 'Studio') return true
        return parseInt(p.bedrooms) <= maxRoomsNum
      })
    }
    if ((filters.minRooms === 'Studio' || filters.maxRooms === 'Studio') && 
        filters.minRooms !== 'min' && filters.maxRooms !== 'max') {
      filtered = filtered.filter(p => 
        p.bedrooms === '0' || p.property_type === 'Studio'
      )
    }

    // Filter by zones
    if (filters.zones.length > 0) {
      filtered = filtered.filter(p => {
        const address = p.address.toLowerCase()
        return filters.zones.some((zone: string) => {
          switch(zone) {
            case 'zone1':
              return /\b(w1|wc1|wc2|ec1|ec2|ec3|ec4|sw1|se1)\b/.test(address)
            case 'zone2':
              return /\b(nw1|n1|e2|se11|sw8|w2|w8|w11)\b/.test(address)
            case 'zone3':
              return /\b(nw2|nw3|nw6|n4|n5|n16|e8|se15|se22|sw4|w3|w4|w6|w12|w14)\b/.test(address)
            default:
              return false
          }
        })
      })
    }

    // Filter by property types
    if (filters.types.length > 0) {
      filtered = filtered.filter(p => {
        const type = p.property_type.toLowerCase()
        return filters.types.some((t: string) => {
          switch(t) {
            case 'detached':
              return type.includes('detached') && !type.includes('semi')
            case 'semi-detached':
              return type.includes('semi-detached')
            case 'terraced':
              return type.includes('terrace') || type.includes('townhouse')
            case 'flat':
              return type.includes('flat') || type.includes('apartment')
            case 'bungalow':
              return type.includes('bungalow')
            case 'student-halls':
              return type.includes('student')
            default:
              return false
          }
        })
      })
    }

    setFilteredProperties(filtered)
  }

  const handleZoneChange = (zone: string, checked: boolean) => {
    setSelectedZones(prev => {
      const newZones = checked ? [...prev, zone] : prev.filter(z => z !== zone)
      filterProperties(properties, {
        minBudget,
        maxBudget,
        minRooms,
        maxRooms,
        zones: newZones,
        types: selectedTypes
      })
      return newZones
    })
  }

  const handleTypeChange = (type: string, checked: boolean) => {
    setSelectedTypes(prev => {
      const newTypes = checked ? [...prev, type] : prev.filter(t => t !== type)
      filterProperties(properties, {
        minBudget,
        maxBudget,
        minRooms,
        maxRooms,
        zones: selectedZones,
        types: newTypes
      })
      return newTypes
    })
  }

  const handleBudgetChange = (type: 'min' | 'max', value: string) => {
    if (type === 'min') {
      setMinBudget(value)
    } else {
      setMaxBudget(value)
    }
    filterProperties(properties, {
      minBudget: type === 'min' ? value : minBudget,
      maxBudget: type === 'max' ? value : maxBudget,
      minRooms,
      maxRooms,
      zones: selectedZones,
      types: selectedTypes
    })
  }

  const handleRoomsChange = (type: 'min' | 'max', value: string) => {
    if (type === 'min') {
      setMinRooms(value)
    } else {
      setMaxRooms(value)
    }
    filterProperties(properties, {
      minBudget,
      maxBudget,
      minRooms: type === 'min' ? value : minRooms,
      maxRooms: type === 'max' ? value : maxRooms,
      zones: selectedZones,
      types: selectedTypes
    })
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar cartItemsCount={0} onCartClick={() => {}} />

      {/* Filters Section */}
      <div className="sticky top-0 bg-black py-3 z-40 border-b shadow-sm">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 xl:grid-cols-7 gap-2">
            <Select value={minBudget} onValueChange={(value) => handleBudgetChange('min', value)}>
              <SelectTrigger className="w-full bg-white">
                <SelectValue placeholder="Мин. цена" />
              </SelectTrigger>
              <SelectContent className="max-h-[200px] overflow-y-auto">
                <SelectItem value="min">Мин. цена</SelectItem>
                {budgetOptions.map((option) => (
                  <SelectItem key={option} value={option}>£{Number(option).toLocaleString()}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={maxBudget} onValueChange={(value) => handleBudgetChange('max', value)}>
              <SelectTrigger className="w-full bg-white">
                <SelectValue placeholder="Макс. цена" />
              </SelectTrigger>
              <SelectContent className="max-h-[200px] overflow-y-auto">
                <SelectItem value="max">Макс. цена</SelectItem>
                {budgetOptions.map((option) => (
                  <SelectItem key={option} value={option}>£{Number(option).toLocaleString()}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={minRooms} onValueChange={(value) => handleRoomsChange('min', value)}>
              <SelectTrigger className="w-full bg-white">
                <SelectValue placeholder="Мин. комнат" />
              </SelectTrigger>
              <SelectContent>
                {minRoomOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option === 'min' ? 'Мин. комнат' : option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={maxRooms} onValueChange={(value) => handleRoomsChange('max', value)}>
              <SelectTrigger className="w-full bg-white">
                <SelectValue placeholder="Макс. комнат" />
              </SelectTrigger>
              <SelectContent>
                {maxRoomOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option === 'max' ? 'Макс. комнат' : option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select 
              value={selectedTypes.join(',')} 
              onValueChange={(value) => {
                const types = value.split(',').filter(t => t);
                types.forEach(type => {
                  if (!selectedTypes.includes(type)) {
                    handleTypeChange(type, true);
                  }
                });
                selectedTypes.forEach(type => {
                  if (!types.includes(type)) {
                    handleTypeChange(type, false);
                  }
                });
              }}
            >
              <SelectTrigger className="w-full bg-white">
                <SelectValue>
                  {selectedTypes.length > 0 
                    ? `Выбрано: ${selectedTypes.length}`
                    : "Тип жилья"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <div className="p-2 space-y-2">
                  <div className="flex items-center">
                    <Checkbox 
                      id="detached"
                      checked={selectedTypes.includes('detached')}
                      onCheckedChange={(checked) => handleTypeChange('detached', checked as boolean)}
                    />
                    <label htmlFor="detached" className="ml-2">🏠 Частный дом</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="semi-detached"
                      checked={selectedTypes.includes('semi-detached')}
                      onCheckedChange={(checked) => handleTypeChange('semi-detached', checked as boolean)}
                    />
                    <label htmlFor="semi-detached" className="ml-2">🏘️ Дуплекс</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="terraced"
                      checked={selectedTypes.includes('terraced')}
                      onCheckedChange={(checked) => handleTypeChange('terraced', checked as boolean)}
                    />
                    <label htmlFor="terraced" className="ml-2">🏢 Таунхаус</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="flat"
                      checked={selectedTypes.includes('flat')}
                      onCheckedChange={(checked) => handleTypeChange('flat', checked as boolean)}
                    />
                    <label htmlFor="flat" className="ml-2">🏙️ Апартаменты</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="bungalow"
                      checked={selectedTypes.includes('bungalow')}
                      onCheckedChange={(checked) => handleTypeChange('bungalow', checked as boolean)}
                    />
                    <label htmlFor="bungalow" className="ml-2">🏡 Бунгало</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="student-halls"
                      checked={selectedTypes.includes('student-halls')}
                      onCheckedChange={(checked) => handleTypeChange('student-halls', checked as boolean)}
                    />
                    <label htmlFor="student-halls" className="ml-2">🏫 Студ. жилье</label>
                  </div>
                </div>
              </SelectContent>
            </Select>

            <Select 
              value={selectedZones.join(',')}
              onValueChange={(value) => {
                const zones = value.split(',').filter(z => z);
                zones.forEach(zone => {
                  if (!selectedZones.includes(zone)) {
                    handleZoneChange(zone, true);
                  }
                });
                selectedZones.forEach(zone => {
                  if (!zones.includes(zone)) {
                    handleZoneChange(zone, false);
                  }
                });
              }}
            >
              <SelectTrigger className="w-full bg-white">
                <SelectValue>
                  {selectedZones.length > 0 
                    ? `Выбрано: ${selectedZones.length}`
                    : "Район"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <div className="p-2 space-y-2">
                  <div className="flex items-center">
                    <Checkbox 
                      id="zone1"
                      checked={selectedZones.includes('zone1')}
                      onCheckedChange={(checked) => handleZoneChange('zone1', checked as boolean)}
                    />
                    <label htmlFor="zone1" className="ml-2">Зона 1</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="zone2"
                      checked={selectedZones.includes('zone2')}
                      onCheckedChange={(checked) => handleZoneChange('zone2', checked as boolean)}
                    />
                    <label htmlFor="zone2" className="ml-2">Зона 2</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="zone3"
                      checked={selectedZones.includes('zone3')}
                      onCheckedChange={(checked) => handleZoneChange('zone3', checked as boolean)}
                    />
                    <label htmlFor="zone3" className="ml-2">Зона 3</label>
                  </div>
                </div>
              </SelectContent>
            </Select>

            <Select 
              value={selectedFurnishing.join(',')}
              onValueChange={(value) => {
                const furnishing = value.split(',').filter(f => f);
                setSelectedFurnishing(furnishing);
              }}
            >
              <SelectTrigger className="w-full bg-white">
                <SelectValue>
                  {selectedFurnishing.length > 0 
                    ? `Выбрано: ${selectedFurnishing.length}`
                    : "Меблировка"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <div className="p-2 space-y-2">
                  <div className="flex items-center">
                    <Checkbox 
                      id="furnished"
                      checked={selectedFurnishing.includes('furnished')}
                      onCheckedChange={(checked) => {
                        setSelectedFurnishing(prev => 
                          checked ? [...prev, 'furnished'] : prev.filter(f => f !== 'furnished')
                        )
                      }}
                    />
                    <label htmlFor="furnished" className="ml-2">🛋️ Меблировано</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="partially-furnished"
                      checked={selectedFurnishing.includes('partially-furnished')}
                      onCheckedChange={(checked) => {
                        setSelectedFurnishing(prev => 
                          checked ? [...prev, 'partially-furnished'] : prev.filter(f => f !== 'partially-furnished')
                        )
                      }}
                    />
                    <label htmlFor="partially-furnished" className="ml-2">🛏️ Частично</label>
                  </div>
                  <div className="flex items-center">
                    <Checkbox 
                      id="unfurnished"
                      checked={selectedFurnishing.includes('unfurnished')}
                      onCheckedChange={(checked) => {
                        setSelectedFurnishing(prev => 
                          checked ? [...prev, 'unfurnished'] : prev.filter(f => f !== 'unfurnished')
                        )
                      }}
                    />
                    <label htmlFor="unfurnished" className="ml-2">🚪 Без мебели</label>
                  </div>
                </div>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Results Section */}
      <main className="flex-grow py-8">
        <div className="container mx-auto px-4">
          {loading ? (
            <div className="text-center">Загрузка...</div>
          ) : (
            <>
              <div className="mb-4">
                <h2 className="text-xl font-semibold">
                  Найдено {filteredProperties.length} объектов
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredProperties.map((property, index) => (
                  <Card key={index} className="flex flex-col h-full group">
                    <CardHeader className="relative">
                      {property.photo_links && (
                        <div className="relative h-48 mb-4 overflow-hidden rounded-md">
                          <Image
                            src={property.photo_links.split(';')[0]}
                            alt={property.address}
                            fill
                            className="object-cover transition-transform duration-300 group-hover:scale-110"
                            onError={(e) => {
                              const img = e.target as HTMLImageElement;
                              const photos = property.photo_links.split(';');
                              const currentIndex = photos.indexOf(img.src);
                              if (currentIndex < photos.length - 1) {
                                img.src = photos[currentIndex + 1];
                              }
                            }}
                          />
                          {property.reduced_info && (
                            <span className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm">
                              {property.reduced_info}
                            </span>
                          )}
                          <div className="absolute bottom-2 right-2 flex gap-2">
                            <button 
                              className="bg-white/90 hover:bg-white p-2 rounded-full transition-colors shadow-sm"
                              onClick={() => {
                                // TODO: Implement like functionality
                                alert('Добавлено в избранное!');
                              }}
                            >
                              <Heart className="w-5 h-5 text-red-500" />
                            </button>
                            <button 
                              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-full transition-colors shadow-lg flex items-center gap-2 text-white font-medium"
                              onClick={() => {
                                // TODO: Implement viewing request
                                alert('Объект добавлен! Наш агент свяжется с вами в ближайшее время.');
                              }}
                            >
                              <Eye className="w-5 h-5" />
                              <span>Заинтересован</span>
                            </button>
                          </div>
                        </div>
                      )}
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-medium px-2 py-1 bg-gray-100 rounded-full">
                          {getPropertyEmoji(property.property_type)} {property.property_type}
                        </span>
                      </div>
                      <CardTitle className="text-lg">{property.address}</CardTitle>
                      <CardDescription>
                        <div className="flex justify-between items-center">
                          <span className="text-lg font-semibold">{property.price}</span>
                          <span className="text-sm text-gray-500">{property.pw_price}</span>
                        </div>
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-grow">
                      <div className="flex gap-4 mb-2">
                        <span>🛏️ {property.bedrooms} спальни</span>
                        <span>🚿 {property.bathrooms} ванные</span>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-3">{property.description}</p>
                    </CardContent>
                    <CardFooter className="flex items-center justify-between border-t pt-4">
                      <div className="flex items-center gap-2">
                        {property.agency_logo && (
                          <div className="relative h-8 w-24">
                            <Image
                              src={property.agency_logo}
                              alt="Agency logo"
                              fill
                              className="object-contain"
                            />
                          </div>
                        )}
                        <span className="text-sm text-gray-500">{property.agency_phone}</span>
                      </div>
                      <Link
                        href={property.ad_link}
                        target="_blank"
                        className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Подробнее
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  )
} 

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Загрузка...</div>}>
      <SearchContent />
    </Suspense>
  )
}
