import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as api from './reservasApi'
import * as academicoApi from '../../services/academicoApi'
import { AcademicPeriodContext, type AcademicPeriodContextValue } from '../../academicPeriodContext'
import { NuevaSolicitudPage, obtenerFechaLocalHoy } from './NuevaSolicitudPage'

vi.mock('./reservasApi', async (original) => ({ ...(await original<typeof import('./reservasApi')>()), crearSolicitud: vi.fn(), consultarDisponibilidad: vi.fn() }))
vi.mock('../../services/academicoApi')
const authUser = { perfilId: 'perfil-1', roles: ['DOCENTE'], permisos: ['SOLICITUD_CREAR'] }
vi.mock('../../auth', async (original) => ({ ...(await original<typeof import('../../auth')>()), useAuth: () => ({ usuario: authUser }) }))
vi.mock('../../components/DashboardLayout', () => ({ DashboardLayout: ({ children }: { children: React.ReactNode }) => <>{children}</> }))

const pisoPB = { id: 'piso-pb', bloqueId: 'b1', numero: 0, descripcion: 'Planta Baja', activo: true }
const piso1 = { id: 'piso-1', bloqueId: 'b1', numero: 1, descripcion: 'Piso 2', activo: true }
const piso2 = { id: 'piso-2', bloqueId: 'b1', numero: 2, descripcion: 'Piso 3', activo: true }

const labPB = { id: 'lab-pb-id', pisoId: 'piso-pb', codigo: 'LAB-PB-01', nombre: 'Lab PB', capacidad: 20, descripcion: '', estado: 'DISPONIBLE' as const, activo: true, creadoEn: '', actualizadoEn: '' }
const lab = { id: 'lab-1', pisoId: 'piso-1', codigo: 'LAB-1', nombre: 'Redes', capacidad: 20, descripcion: '', estado: 'DISPONIBLE' as const, activo: true, creadoEn: '', actualizadoEn: '' }
const labP2 = { id: 'lab-p2-id', pisoId: 'piso-2', codigo: 'LAB-P2-01', nombre: 'Lab Software', capacidad: 25, descripcion: '', estado: 'DISPONIBLE' as const, activo: true, creadoEn: '', actualizadoEn: '' }
const docente = { id: 'doc-1', perfilId: 'perfil-1', codigoDocente: 'DOC-01', nombres: 'Carlos', apellidos: 'Andrade', activo: true }
const materia = { id: 'mat-1', carreraId: 'c1', codigo: 'MAT-1', nombre: 'Redes I', numeroHoras: 40, activo: true }
const periodo = { id: 'per-1', codigo: '2026-A', nombre: 'Primer período', fechaInicio: '', fechaFin: '', estado: 'ACTIVO' as const }
const horario = { id: 'h1', materiaId: 'mat-1', periodoLectivoId: 'per-1', laboratorioId: 'lab-1', docenteId: 'doc-1', diaSemana: 'LUNES', horaInicio: '08:00', horaFin: '10:00', paralelo: 'A', activo: true }

describe('NuevaSolicitudPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(academicoApi.obtenerPisos).mockResolvedValue([pisoPB, piso1, piso2])
    vi.mocked(academicoApi.obtenerLaboratorios).mockResolvedValue([lab])
    vi.mocked(academicoApi.obtenerMaterias).mockResolvedValue([materia])
    vi.mocked(academicoApi.obtenerPeriodoActual).mockResolvedValue(periodo)
    vi.mocked(academicoApi.obtenerDocentePorPerfil).mockResolvedValue(docente)
    vi.mocked(academicoApi.obtenerDocentes).mockResolvedValue([docente])
    vi.mocked(academicoApi.obtenerHorariosDocente).mockResolvedValue([horario])
  })

  function renderForm(contextValue?: Partial<AcademicPeriodContextValue>) {
    const value: AcademicPeriodContextValue = {
      periodos: [],
      periodoVigente: null,
      periodoSeleccionado: null,
      seleccionarPeriodo: vi.fn(),
      cargando: false,
      ...contextValue,
    }
    return render(
      <AcademicPeriodContext.Provider value={value}>
        <MemoryRouter initialEntries={['/reservas/nueva']}>
          <Routes>
            <Route path="/reservas/nueva" element={<NuevaSolicitudPage />} />
            <Route path="/solicitudes/:id" element={<div>Detalle Solicitud</div>} />
          </Routes>
        </MemoryRouter>
      </AcademicPeriodContext.Provider>,
    )
  }

  async function completar() {
    expect(await screen.findByRole('option', { name: 'MAT-1 — Redes I' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /LAB-1 — Redes/ })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Carlos Andrade (DOC-01)' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Materia'), { target: { value: 'mat-1' } })
    fireEvent.change(screen.getByLabelText('Laboratorio'), { target: { value: 'lab-1' } })
    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2099-08-20' } })
    fireEvent.change(screen.getByLabelText('Hora inicio'), { target: { value: '08:00' } })
    fireEvent.change(screen.getByLabelText('Hora fin'), { target: { value: '10:00' } })
    fireEvent.change(screen.getByLabelText('Motivo'), { target: { value: 'Clase práctica' } })
  }

  it('resuelve docente y carga selectores humanos sin inputs UUID manuales mostrando nombre humano', async () => {
    renderForm()
    expect(await screen.findByRole('option', { name: 'MAT-1 — Redes I' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /LAB-1 — Redes/ })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Carlos Andrade (DOC-01)' })).toBeInTheDocument()
    expect(screen.getByDisplayValue('2026-A — Primer período')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText(/UUID/i)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/UUID/i)).not.toBeInTheDocument()
  })

  it('envía IDs resueltos con Idempotency-Key y navega al detalle', async () => {
    vi.mocked(api.crearSolicitud).mockResolvedValue({
      id: 'sol-1',
      laboratorioId: 'lab-1',
      docenteId: 'doc-1',
      solicitanteId: 'perfil-1',
      materiaId: 'mat-1',
      periodoLectivoId: 'per-1',
      fechaReserva: '2099-08-20',
      horaInicio: '08:00',
      horaFin: '10:00',
      numeroParticipantes: 1,
      motivo: 'Clase práctica',
      observacion: '',
      estado: 'PENDIENTE',
      propuestaFecha: null,
      propuestaHoraInicio: null,
      propuestaHoraFin: null,
      propuestaLaboratorioId: null,
      propuestaObservacion: null,
      reservaId: null,
      creadaEn: '',
      actualizadaEn: '',
      version: 0,
    })

    renderForm()
    await completar()
    fireEvent.click(screen.getByRole('button', { name: 'Crear solicitud' }))

    expect(await screen.findByText('Detalle Solicitud')).toBeInTheDocument()
    expect(api.crearSolicitud).toHaveBeenCalledWith(
      expect.objectContaining({
        laboratorioId: 'lab-1',
        docenteId: 'doc-1',
        materiaId: 'mat-1',
        solicitanteId: 'perfil-1',
        fechaReserva: '2099-08-20',
        horaInicio: '08:00',
        horaFin: '10:00',
        motivo: 'Clase práctica',
      }),
      expect.stringMatching(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i),
    )
  })

  it('comprueba disponibilidad con una explicación humana', async () => {
    vi.mocked(api.consultarDisponibilidad).mockResolvedValue({
      laboratorioId: 'lab-1',
      fecha: '2099-08-20',
      horaInicio: '08:00',
      horaFin: '10:00',
      disponible: false,
      motivo: 'Existe una reserva',
    })
    renderForm()
    await completar()
    fireEvent.click(screen.getByRole('button', { name: 'Comprobar disponibilidad' }))
    expect(await screen.findByText('No disponible: Existe una reserva')).toBeInTheDocument()
  })

  it('evita doble envío del mismo intento lógico', async () => {
    vi.mocked(api.crearSolicitud).mockReturnValue(new Promise(() => {}))
    renderForm()
    await completar()
    fireEvent.click(screen.getByRole('button', { name: 'Crear solicitud' }))
    fireEvent.click(screen.getByRole('button', { name: 'Enviando...' }))
    expect(api.crearSolicitud).toHaveBeenCalledTimes(1)
  })
  it('filtra laboratorios por piso usando exclusivamente pisoId, limpia selección incompatible y restaura al volver a todos', async () => {
    vi.mocked(academicoApi.obtenerLaboratorios).mockResolvedValue([labPB, lab, labP2])
    renderForm()

    // 1. "Todos los pisos" muestra todos los laboratorios con su piso humano real
    expect(await screen.findByRole('option', { name: 'Todos los pisos' })).toBeInTheDocument()
    const selectPiso = screen.getByLabelText('Piso')
    const selectLab = screen.getByLabelText('Laboratorio') as HTMLSelectElement

    expect(screen.getByRole('option', { name: 'LAB-PB-01 — Lab PB — Piso 1 · Planta Baja' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'LAB-1 — Redes — Piso 2' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'LAB-P2-01 — Lab Software — Piso 3' })).toBeInTheDocument()

    // 2. Seleccionar Piso 1 · Planta Baja muestra solamente sus laboratorios (pisoId === 'piso-pb', numero 0)
    fireEvent.change(selectPiso, { target: { value: 'piso-pb' } })
    expect(screen.getByRole('option', { name: 'LAB-PB-01 — Lab PB — Piso 1 · Planta Baja' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /LAB-1 — Redes/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /LAB-P2-01 — Lab Software/ })).not.toBeInTheDocument()

    // Seleccionar el laboratorio de Planta Baja
    fireEvent.change(selectLab, { target: { value: 'lab-pb-id' } })
    expect(selectLab.value).toBe('lab-pb-id')

    // 3 y 4. Seleccionar otro piso cambia correctamente el conjunto visible usando pisoId
    fireEvent.change(selectPiso, { target: { value: 'piso-1' } })
    expect(screen.queryByRole('option', { name: /LAB-PB-01 — Lab PB/ })).not.toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'LAB-1 — Redes — Piso 2' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /LAB-P2-01 — Lab Software/ })).not.toBeInTheDocument()

    // 5. Cambiar a piso incompatible elimina la selección de laboratorio previa para no dejar selección invisible
    expect(selectLab.value).toBe('')

    // 6. Volver a "Todos los pisos" vuelve a mostrar todos
    fireEvent.change(selectPiso, { target: { value: '' } })
    expect(screen.getByRole('option', { name: 'LAB-PB-01 — Lab PB — Piso 1 · Planta Baja' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'LAB-1 — Redes — Piso 2' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'LAB-P2-01 — Lab Software — Piso 3' })).toBeInTheDocument()
  })

  it('crear solicitud con filtro de piso activo envía el laboratorioId real y preserva periodo e idempotencia', async () => {
    vi.mocked(academicoApi.obtenerLaboratorios).mockResolvedValue([labPB, lab, labP2])
    vi.mocked(api.crearSolicitud).mockResolvedValue({
      id: 'sol-pb-1',
      laboratorioId: 'lab-pb-id',
      docenteId: 'doc-1',
      solicitanteId: 'perfil-1',
      materiaId: 'mat-1',
      periodoLectivoId: 'per-1',
      fechaReserva: '2099-09-10',
      horaInicio: '09:00',
      horaFin: '11:00',
      numeroParticipantes: 1,
      motivo: 'Laboratorio Planta Baja',
      observacion: '',
      estado: 'PENDIENTE',
      propuestaFecha: null,
      propuestaHoraInicio: null,
      propuestaHoraFin: null,
      propuestaLaboratorioId: null,
      propuestaObservacion: null,
      reservaId: null,
      creadaEn: '',
      actualizadaEn: '',
      version: 0,
    })

    renderForm()
    expect(await screen.findByRole('option', { name: 'Todos los pisos' })).toBeInTheDocument()

    // Filtrar por Planta Baja
    fireEvent.change(screen.getByLabelText('Piso'), { target: { value: 'piso-pb' } })
    expect(screen.getByRole('option', { name: 'LAB-PB-01 — Lab PB — Piso 1 · Planta Baja' })).toBeInTheDocument()

    // Completar formulario con lab de PB
    fireEvent.change(screen.getByLabelText('Materia'), { target: { value: 'mat-1' } })
    fireEvent.change(screen.getByLabelText('Laboratorio'), { target: { value: 'lab-pb-id' } })
    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2099-09-10' } })
    fireEvent.change(screen.getByLabelText('Hora inicio'), { target: { value: '09:00' } })
    fireEvent.change(screen.getByLabelText('Hora fin'), { target: { value: '11:00' } })
    fireEvent.change(screen.getByLabelText('Motivo'), { target: { value: 'Laboratorio Planta Baja' } })

    fireEvent.click(screen.getByRole('button', { name: 'Crear solicitud' }))

    expect(await screen.findByText('Detalle Solicitud')).toBeInTheDocument()
    expect(api.crearSolicitud).toHaveBeenCalledWith(
      expect.objectContaining({
        laboratorioId: 'lab-pb-id',
        docenteId: 'doc-1',
        materiaId: 'mat-1',
        periodoLectivoId: 'per-1',
        fechaReserva: '2099-09-10',
        horaInicio: '09:00',
        horaFin: '11:00',
        motivo: 'Laboratorio Planta Baja',
      }),
      expect.stringMatching(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i),
    )
  })

  it('asigna min y max en input de fecha cuando fechaInicio es futura', async () => {
    const periodoFuturo = {
      id: 'per-futuro',
      codigo: '2027-B',
      nombre: 'Periodo Futuro',
      fechaInicio: '2027-01-10',
      fechaFin: '2027-06-30',
      estado: 'ACTIVO' as const,
    }
    renderForm({ periodoSeleccionado: periodoFuturo })
    const fechaInput = (await screen.findByLabelText('Fecha')) as HTMLInputElement
    expect(fechaInput.min).toBe('2027-01-10')
    expect(fechaInput.max).toBe('2027-06-30')
  })

  it('asigna min con la fecha de hoy cuando fechaInicio está en el pasado', async () => {
    const ahora = new Date()
    const hoy = `${ahora.getFullYear()}-${String(ahora.getMonth() + 1).padStart(2, '0')}-${String(ahora.getDate()).padStart(2, '0')}`
    const periodoPasadoInicio = {
      id: 'per-vigente',
      codigo: '2026-A',
      nombre: 'Periodo Vigente',
      fechaInicio: '2020-01-01',
      fechaFin: '2099-12-31',
      estado: 'ACTIVO' as const,
    }
    renderForm({ periodoSeleccionado: periodoPasadoInicio })
    const fechaInput = (await screen.findByLabelText('Fecha')) as HTMLInputElement
    expect(fechaInput.min).toBe(hoy)
    expect(fechaInput.max).toBe('2099-12-31')
  })

  it('rechaza submit si fechaReserva es anterior a fechaMinima', async () => {
    const periodoPrueba = {
      id: 'per-test',
      codigo: '2027-A',
      nombre: 'Periodo 2027',
      fechaInicio: '2027-02-01',
      fechaFin: '2027-07-31',
      estado: 'ACTIVO' as const,
    }
    renderForm({ periodoSeleccionado: periodoPrueba })
    await completar()
    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2027-01-15' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Crear solicitud' }).closest('form')!)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'La fecha de la reserva debe estar comprendida entre 2027-02-01 y 2027-07-31 para el período académico seleccionado.'
    )
    expect(api.crearSolicitud).not.toHaveBeenCalled()
  })

  it('rechaza submit si fechaReserva es posterior a fechaFin', async () => {
    const periodoPrueba = {
      id: 'per-test',
      codigo: '2027-A',
      nombre: 'Periodo 2027',
      fechaInicio: '2027-02-01',
      fechaFin: '2027-07-31',
      estado: 'ACTIVO' as const,
    }
    renderForm({ periodoSeleccionado: periodoPrueba })
    await completar()
    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2027-08-01' } })
    fireEvent.submit(screen.getByRole('button', { name: 'Crear solicitud' }).closest('form')!)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'La fecha de la reserva debe estar comprendida entre 2027-02-01 y 2027-07-31 para el período académico seleccionado.'
    )
    expect(api.crearSolicitud).not.toHaveBeenCalled()
  })

  it('permite enviar solicitud con fecha válida dentro del per\u00edodo', async () => {
    const periodoPrueba = {
      id: 'per-test',
      codigo: '2027-A',
      nombre: 'Periodo 2027',
      fechaInicio: '2027-02-01',
      fechaFin: '2027-07-31',
      estado: 'ACTIVO' as const,
    }
    vi.mocked(api.crearSolicitud).mockResolvedValue({
      id: 'sol-ok',
      laboratorioId: 'lab-1',
      docenteId: 'doc-1',
      solicitanteId: 'perfil-1',
      materiaId: 'mat-1',
      periodoLectivoId: 'per-test',
      fechaReserva: '2027-03-15',
      horaInicio: '08:00',
      horaFin: '10:00',
      numeroParticipantes: 1,
      motivo: 'Clase práctica',
      observacion: '',
      estado: 'PENDIENTE',
      propuestaFecha: null,
      propuestaHoraInicio: null,
      propuestaHoraFin: null,
      propuestaLaboratorioId: null,
      propuestaObservacion: null,
      reservaId: null,
      creadaEn: '',
      actualizadaEn: '',
      version: 0,
    })
    renderForm({ periodoSeleccionado: periodoPrueba })
    await completar()
    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2027-03-15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear solicitud' }))

    expect(await screen.findByText('Detalle Solicitud')).toBeInTheDocument()
    expect(api.crearSolicitud).toHaveBeenCalledWith(
      expect.objectContaining({
        periodoLectivoId: 'per-test',
        fechaReserva: '2027-03-15',
      }),
      expect.any(String),
    )
  })

  it('rechaza comprobar disponibilidad si fechaReserva está fuera del per\u00edodo', async () => {
    const periodoPrueba = {
      id: 'per-test',
      codigo: '2027-A',
      nombre: 'Periodo 2027',
      fechaInicio: '2027-02-01',
      fechaFin: '2027-07-31',
      estado: 'ACTIVO' as const,
    }
    renderForm({ periodoSeleccionado: periodoPrueba })
    await completar()
    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2027-08-10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Comprobar disponibilidad' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'La fecha de la reserva debe estar comprendida entre 2027-02-01 y 2027-07-31 para el período académico seleccionado.'
    )
    expect(api.consultarDisponibilidad).not.toHaveBeenCalled()
  })

  it('muestra advertencia y deshabilita botones cuando hoy supera fechaFin del per\u00edodo', async () => {
    const periodoVencido = {
      id: 'per-vencido',
      codigo: '2020-A',
      nombre: 'Periodo Vencido',
      fechaInicio: '2020-01-01',
      fechaFin: '2020-06-30',
      estado: 'FINALIZADO' as const,
    }
    renderForm({ periodoSeleccionado: periodoVencido })
    expect(await screen.findByText('No existen fechas disponibles para reservas dentro de este período académico.')).toBeInTheDocument()
    const btnSubmit = screen.getByRole('button', { name: 'Crear solicitud' })
    const btnCheck = screen.getByRole('button', { name: 'Comprobar disponibilidad' })
    const inputFecha = screen.getByLabelText('Fecha') as HTMLInputElement

    expect(btnSubmit).toBeDisabled()
    expect(btnCheck).toBeDisabled()
    expect(inputFecha).toBeDisabled()
  })

  it('limpia fechaReserva si el cambio de per\u00edodo la deja fuera de rango', async () => {
    const periodo1 = {
      id: 'per-1',
      codigo: '2027-A',
      nombre: 'Periodo 1',
      fechaInicio: '2027-01-01',
      fechaFin: '2027-06-30',
      estado: 'ACTIVO' as const,
    }
    const periodo2 = {
      id: 'per-2',
      codigo: '2027-B',
      nombre: 'Periodo 2',
      fechaInicio: '2027-07-01',
      fechaFin: '2027-12-31',
      estado: 'ACTIVO' as const,
    }
    const { rerender } = renderForm({ periodoSeleccionado: periodo1 })
    await completar()
    const inputFecha = screen.getByLabelText('Fecha') as HTMLInputElement
    fireEvent.change(inputFecha, { target: { value: '2027-03-15' } })
    expect(inputFecha.value).toBe('2027-03-15')

    // Rerender with periodo2
    rerender(
      <AcademicPeriodContext.Provider
        value={{
          periodos: [periodo1, periodo2],
          periodoVigente: null,
          periodoSeleccionado: periodo2,
          seleccionarPeriodo: vi.fn(),
          cargando: false,
        }}
      >
        <MemoryRouter initialEntries={['/reservas/nueva']}>
          <Routes>
            <Route path="/reservas/nueva" element={<NuevaSolicitudPage />} />
          </Routes>
        </MemoryRouter>
      </AcademicPeriodContext.Provider>,
    )

    // 2027-03-15 is before periodo2.fechaInicio (2027-07-01), so fechaReserva should be reset to ''
    expect(inputFecha.value).toBe('')
  })

  it('considera la fecha local y no el día siguiente de UTC en horas de la noche', async () => {
    const fechaUtc = new Date('2026-09-08T01:00:00.000Z')
    const spyYear = vi.spyOn(Date.prototype, 'getFullYear').mockReturnValue(2026)
    const spyMonth = vi.spyOn(Date.prototype, 'getMonth').mockReturnValue(8)
    const spyDate = vi.spyOn(Date.prototype, 'getDate').mockReturnValue(7)

    try {
      expect(fechaUtc.toISOString().slice(0, 10)).toBe('2026-09-08')
      expect(obtenerFechaLocalHoy()).toBe('2026-09-07')

      const periodoVigente = {
        id: 'per-vigente',
        codigo: '2026-B',
        nombre: 'Periodo 2026-B',
        fechaInicio: '2026-09-01',
        fechaFin: '2027-01-31',
        estado: 'ACTIVO' as const,
      }
      renderForm({ periodoSeleccionado: periodoVigente })

      const inputFecha = (await screen.findByLabelText('Fecha')) as HTMLInputElement
      expect(inputFecha.min).toBe('2026-09-07')
      expect(inputFecha.min).not.toBe('2026-09-08')
    } finally {
      spyYear.mockRestore()
      spyMonth.mockRestore()
      spyDate.mockRestore()
    }
  })
})
