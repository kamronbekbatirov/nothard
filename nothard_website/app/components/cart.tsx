import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { Button } from "../components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "../components/ui/card"
import { Separator } from "../components/ui/separator"
import { ScrollArea } from "../components/ui/scroll-area"
import { toast } from "../components/ui/use-toast"

interface CartItem {
  name: string
  price: string
  priceUSD: string
  priceUZS: string
  type: 'package' | 'service'
}

interface CartProps {
  items: CartItem[]
  onRemoveItem: (item: CartItem) => void
  onClose: () => void
}

export function Cart({ items, onRemoveItem, onClose }: CartProps) {
  const [total, setTotal] = useState({ gbp: 0, usd: 0, uzs: 0 })

  useEffect(() => {
    const newTotal = items.reduce((sum, item) => {
      const priceGBP = parseFloat(item.price.replace(/[^0-9.-]+/g, ""))
      const priceUSD = parseFloat(item.priceUSD.replace(/[^0-9.-]+/g, ""))
      const priceUZS = parseFloat(item.priceUZS.replace(/[^0-9.-]+/g, "").replace(/,/g, ""))
      return {
        gbp: sum.gbp + priceGBP,
        usd: sum.usd + priceUSD,
        uzs: sum.uzs + priceUZS
      }
    }, { gbp: 0, usd: 0, uzs: 0 })
    setTotal(newTotal)
  }, [items])

  const handleRemoveItem = (item: CartItem) => {
    onRemoveItem(item)
    toast({
      title: "Элемент удален",
      description: `${item.name} был удален из корзины.`,
    })
  }

  const handleCheckout = () => {
    toast({
      title: "Оформление заказа",
      description: "Функция оформления заказа пока не реализована.",
    })
  }

  return (
    <Card className="w-full sm:w-[350px] h-[100vh] sm:h-[600px] fixed right-0 top-0 sm:right-4 sm:top-20 z-50 flex flex-col">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Корзина</CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>{items.length} элемент(ов) в корзине</CardDescription>
      </CardHeader>
      <CardContent className="flex-grow overflow-auto">
        <ScrollArea className="h-full w-full pr-4">
          {items.map((item, index) => (
            <div key={index} className="mb-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{item.name}</h3>
                  <p className="text-sm text-muted-foreground">{item.price} / {item.priceUSD} / {item.priceUZS}</p>
                  <p className="text-xs text-muted-foreground capitalize">{item.type}</p>
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleRemoveItem(item)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              {index < items.length - 1 && <Separator className="my-2" />}
            </div>
          ))}
        </ScrollArea>
      </CardContent>
      <CardFooter className="flex flex-col mt-auto">
        <div className="flex justify-between items-center w-full mb-4">
          <span className="font-semibold">Итого:</span>
          <div className="text-right">
            <div>£{total.gbp.toFixed(2)} / ${total.usd.toFixed(2)}</div>
            <div className="text-sm text-muted-foreground">{total.uzs.toLocaleString()} сум</div>
          </div>
        </div>
        <Button className="w-full">Оформить заказ</Button>
      </CardFooter>
    </Card>
  )
}
<style jsx global>{`
  @media (max-width: 640px) {
    body {
      overflow: hidden;
    }
  }
`}</style>