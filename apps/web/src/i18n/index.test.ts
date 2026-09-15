import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('idioma persistido', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    vi.doMock('i18next', () => {
      const instance = {
        isInitialized: false,
        language: undefined as string | undefined,
        use: () => instance,
        init: (options: { lng: string }) => {
          instance.language = options.lng
          instance.isInitialized = true
          return Promise.resolve(instance)
        },
      }
      return { default: instance }
    })
  })

  it('inicia en inglés cuando la preferencia persistida lo indica', async () => {
    localStorage.setItem('scli-preferencias', JSON.stringify({ state: { idioma: 'en' } }))

    const { default: i18n } = await import('./index')

    expect(i18n.language).toBe('en')
  })

  it('usa español para una preferencia válida distinta de inglés o ausente', async () => {
    localStorage.setItem('scli-preferencias', JSON.stringify({ state: { idioma: 'fr' } }))
    const { default: i18n } = await import('./index')
    expect(i18n.language).toBe('es')

    vi.resetModules()
    localStorage.clear()
    const { default: i18nSinPreferencia } = await import('./index')
    expect(i18nSinPreferencia.language).toBe('es')
  })

  it('usa español si el almacenamiento contiene JSON inválido', async () => {
    localStorage.setItem('scli-preferencias', '{invalido')

    const { default: i18n } = await import('./index')

    expect(i18n.language).toBe('es')
  })
})