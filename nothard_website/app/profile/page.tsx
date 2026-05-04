'use client'

import { Navbar } from "../components/navbar"
import { Footer } from "../components/footer"
import Profile from "../components/profile"

export default function ProfilePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar cartItemsCount={0} onCartClick={() => {}} />
      <main className="flex-grow">
        <Profile />
      </main>
      <Footer />
    </div>
  )
}