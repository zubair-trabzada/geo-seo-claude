import { NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import bcrypt from 'bcryptjs'
import { prisma } from '@/lib/db'
import type { JWT } from 'next-auth/jwt'
import type { Session } from 'next-auth'

// ── Extend next-auth types ────────────────────────────────────────────────────
declare module 'next-auth' {
  interface Session {
    user: {
      id: string
      email: string
      name?: string | null
      image?: string | null
      role: string
      clientId: string | null
    }
  }

  interface User {
    id: string
    email: string
    role: string
    clientId: string | null
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string
    role: string
    clientId: string | null
  }
}

// ── Auth options ──────────────────────────────────────────────────────────────
export const authOptions: NextAuthOptions = {
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },

  pages: {
    signIn: '/login',
    error: '/login',
  },

  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },

      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        const user = await prisma.user.findUnique({
          where: { email: credentials.email.toLowerCase().trim() },
        })

        if (!user) return null

        const passwordValid = await bcrypt.compare(
          credentials.password,
          user.passwordHash,
        )
        if (!passwordValid) return null

        return {
          id: user.id,
          email: user.email,
          role: user.role,
          clientId: user.clientId ?? null,
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user }): Promise<JWT> {
      if (user) {
        token.id = user.id
        token.role = user.role
        token.clientId = user.clientId ?? null
      }
      return token
    },

    async session({ session, token }): Promise<Session> {
      session.user.id = token.id
      session.user.role = token.role
      session.user.clientId = token.clientId
      return session
    },
  },
}
