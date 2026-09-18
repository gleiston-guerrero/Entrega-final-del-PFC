import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from './apiClient'
import * as academico from './academicoApi'
import * as operational from './operationalApi'
import * as usuarios from './usuariosApi'

vi.mock('./apiClient', async (importOriginal) => {
  const original = await importOriginal<typeof import('./apiClient')>()
  return { ...original, apiRequest: vi.fn() }
})

const mockRequest = vi.mocked(apiRequest)

type RequestExpectation = [path: string, method?: string, body?: string]

function expectRequests(expected: RequestExpectation[]) {
  expect(mockRequest).toHaveBeenCalledTimes(expected.length)
  expected.forEach(([path, method = 'GET', body], index) => {
    const call = mockRequest.mock.calls[index]
    expect(call?.[0], `missing request ${method} ${path}`).toBe(path)
    expect(call?.[1]?.method ?? 'GET').toBe(method)
    if (body !== undefined) expect(call?.[1]?.body).toBe(body)
  })
}

describe('cobertura exhaustiva de endpoints de servicios', () => {
  // Los mocks usan valores distintos por clave para demostrar qué propiedad
  // consume realmente cada adapter: academico/usuariosApi leen `content`
  // (paginación estilo Spring), mientras que operationalApi lee `contenido`
  // (paginación en español). Un cambio accidental de una por otra rompe las
  // aserciones de retorno de abajo.
  beforeEach(() => {
    mockRequest.mockReset()
    mockRequest.mockResolvedValue({ content: ['item-content'], contenido: ['item-contenido'] })
  })

  it('cubre funciones CRUD de academicoApi', async () => {
    await academico.obtenerDocentesPlanificacion()
    expect(await academico.obtenerLaboratorios()).toEqual(['item-content'])
    expect(await academico.obtenerDocentes()).toEqual(['item-content'])
    expect(await academico.obtenerMaterias()).toEqual(['item-content'])
    expect(await academico.obtenerPeriodos()).toEqual(['item-content'])
    await academico.crearPeriodo({
      codigo: '2026-1',
      nombre: 'P1',
      fechaInicio: '2026-01-01',
      fechaFin: '2026-06-30',
      estado: 'ACTIVO',
      ppaCodigo: 'PPA1',
      ppaNombre: 'PPA Uno',
      cicloAcademico: 1,
    })
    await academico.actualizarPeriodo('p-1', {
      codigo: '2026-1',
      nombre: 'P1',
      fechaInicio: '2026-01-01',
      fechaFin: '2026-06-30',
      estado: 'ACTIVO',
      ppaCodigo: 'PPA1',
      ppaNombre: 'PPA Uno',
      cicloAcademico: 1,
    })
    expect(await academico.obtenerCarreras()).toEqual(['item-content'])
    expect(await academico.obtenerPisos()).toEqual(['item-content'])
    expect(await academico.obtenerCampus()).toEqual(['item-content'])
    expect(await academico.obtenerEquipos()).toEqual(['item-content'])
    expect(await academico.obtenerTiposEquipo()).toEqual(['item-content'])
    expect(await academico.obtenerBloques()).toEqual(['item-content'])
    expect(await academico.obtenerFacultades()).toEqual(['item-content'])
    await academico.crearLaboratorio({ pisoId: 'p1', codigo: 'L1', nombre: 'Lab 1', capacidad: 20, descripcion: 'Desc' })
    await academico.actualizarLaboratorio('l-1', { pisoId: 'p1', codigo: 'L1', nombre: 'Lab 1', capacidad: 20, descripcion: 'Desc' })
    await academico.cambiarEstadoLaboratorio('l-1', 'DISPONIBLE')
    await academico.crearEquipo({
      laboratorioId: 'l1', tipoEquipoId: 't1', codigoInventario: 'EQ1', numeroSerie: 'S1',
      marca: 'M', modelo: 'Mod', procesador: 'i7', memoriaRam: '16GB', almacenamiento: '512GB',
      direccionIp: '1.1.1.1', direccionMac: 'AA:BB:CC', observacion: 'Obs',
    })
    await academico.actualizarEquipo('e-1', {
      laboratorioId: 'l1', tipoEquipoId: 't1', codigoInventario: 'EQ1', numeroSerie: 'S1',
      marca: 'M', modelo: 'Mod', procesador: 'i7', memoriaRam: '16GB', almacenamiento: '512GB',
      direccionIp: '1.1.1.1', direccionMac: 'AA:BB:CC', observacion: 'Obs',
    })
    await academico.cambiarEstadoEquipo('e-1', 'OPERATIVO')
    await academico.crearCampus({ codigo: 'C1', nombre: 'Campus 1', direccion: 'Dir' })
    await academico.actualizarCampus('c-1', { codigo: 'C1', nombre: 'Campus 1', direccion: 'Dir' })
    await academico.crearPiso({ bloqueId: 'b1', numero: 1, descripcion: 'Piso 1' })
    await academico.actualizarPiso('p-1', { bloqueId: 'b1', numero: 1, descripcion: 'Piso 1' })
    await academico.crearCarrera({ facultadId: 'f1', codigo: 'CAR1', nombre: 'Carrera 1', descripcion: 'Desc' })
    await academico.actualizarCarrera('c-1', { facultadId: 'f1', codigo: 'CAR1', nombre: 'Carrera 1', descripcion: 'Desc' })
    await academico.crearMateria({ carreraId: 'c1', codigo: 'MAT1', nombre: 'Materia 1', numeroHoras: 4, nivel: 1 })
    await academico.actualizarMateria('m-1', { carreraId: 'c1', codigo: 'MAT1', nombre: 'Materia 1', numeroHoras: 4, nivel: 1 })

    await academico.obtenerOcupacionHistorica(15)
    expectRequests([
      ['/api/v1/docentes/planificacion'], ['/api/v1/laboratorios?size=100'], ['/api/v1/docentes?size=100'], ['/api/v1/materias?size=100'], ['/api/v1/periodos-lectivos?size=100'],
      ['/api/v1/periodos-lectivos', 'POST', JSON.stringify({ codigo: '2026-1', nombre: 'P1', fechaInicio: '2026-01-01', fechaFin: '2026-06-30', estado: 'ACTIVO', ppaCodigo: 'PPA1', ppaNombre: 'PPA Uno', cicloAcademico: 1 })],
      ['/api/v1/periodos-lectivos/p-1', 'PUT', JSON.stringify({ codigo: '2026-1', nombre: 'P1', fechaInicio: '2026-01-01', fechaFin: '2026-06-30', estado: 'ACTIVO', ppaCodigo: 'PPA1', ppaNombre: 'PPA Uno', cicloAcademico: 1 })],
      ['/api/v1/carreras?size=100'], ['/api/v1/pisos?size=100'], ['/api/v1/campus?size=100'], ['/api/v1/equipos?size=100'], ['/api/v1/tipos-equipo?size=100'], ['/api/v1/bloques?size=100'], ['/api/v1/facultades?size=100'],
      ['/api/v1/laboratorios', 'POST', JSON.stringify({ pisoId: 'p1', codigo: 'L1', nombre: 'Lab 1', capacidad: 20, descripcion: 'Desc' })],
      ['/api/v1/laboratorios/l-1', 'PUT', JSON.stringify({ pisoId: 'p1', codigo: 'L1', nombre: 'Lab 1', capacidad: 20, descripcion: 'Desc' })],
      ['/api/v1/laboratorios/l-1/estado', 'PATCH', JSON.stringify({ estado: 'DISPONIBLE' })],
      ['/api/v1/equipos', 'POST', JSON.stringify({ laboratorioId: 'l1', tipoEquipoId: 't1', codigoInventario: 'EQ1', numeroSerie: 'S1', marca: 'M', modelo: 'Mod', procesador: 'i7', memoriaRam: '16GB', almacenamiento: '512GB', direccionIp: '1.1.1.1', direccionMac: 'AA:BB:CC', observacion: 'Obs' })],
      ['/api/v1/equipos/e-1', 'PUT', JSON.stringify({ laboratorioId: 'l1', tipoEquipoId: 't1', codigoInventario: 'EQ1', numeroSerie: 'S1', marca: 'M', modelo: 'Mod', procesador: 'i7', memoriaRam: '16GB', almacenamiento: '512GB', direccionIp: '1.1.1.1', direccionMac: 'AA:BB:CC', observacion: 'Obs' })],
      ['/api/v1/equipos/e-1/estado', 'PATCH', JSON.stringify({ estado: 'OPERATIVO' })],
      ['/api/v1/campus', 'POST', JSON.stringify({ codigo: 'C1', nombre: 'Campus 1', direccion: 'Dir' })], ['/api/v1/campus/c-1', 'PUT', JSON.stringify({ codigo: 'C1', nombre: 'Campus 1', direccion: 'Dir' })],
      ['/api/v1/pisos', 'POST', JSON.stringify({ bloqueId: 'b1', numero: 1, descripcion: 'Piso 1' })], ['/api/v1/pisos/p-1', 'PUT', JSON.stringify({ bloqueId: 'b1', numero: 1, descripcion: 'Piso 1' })],
      ['/api/v1/carreras', 'POST', JSON.stringify({ facultadId: 'f1', codigo: 'CAR1', nombre: 'Carrera 1', descripcion: 'Desc' })], ['/api/v1/carreras/c-1', 'PUT', JSON.stringify({ facultadId: 'f1', codigo: 'CAR1', nombre: 'Carrera 1', descripcion: 'Desc' })],
      ['/api/v1/materias', 'POST', JSON.stringify({ carreraId: 'c1', codigo: 'MAT1', nombre: 'Materia 1', numeroHoras: 4, nivel: 1 })], ['/api/v1/materias/m-1', 'PUT', JSON.stringify({ carreraId: 'c1', codigo: 'MAT1', nombre: 'Materia 1', numeroHoras: 4, nivel: 1 })],
      ['/api/v1/laboratorios/metricas/ocupacion?rangoMinutos=15'],
    ])
  })

  it('cubre funciones de operationalApi para planificacion, asistencias, notificaciones e incidentes', async () => {
    await operational.listarPlanificacionesAgregadas()
    await operational.iniciarPlanificacion('per-1')
    await operational.enviarPlanificacionCompleta('plan-1')
    await operational.retirarPlanificacionCompleta('plan-1')
    await operational.resetPlanificacionDemo('plan-1')
    await operational.obtenerDisponibilidadPlanificacion({
      planificacionId: 'plan-1', periodoId: 'per-1', dia: 'LUNES', horaInicio: '07:00', horaFin: '09:00',
    })
    await operational.aprobarPlanificacionPiso('plan-1')
    await operational.rechazarPlanificacionPiso('plan-1', 'Motivo rechazo')
    await operational.proponerCambioPlanificacionPiso('plan-1', { bloqueId: 'b-1', observacion: 'Obs' })
    await operational.listarPlanificaciones()
    await operational.crearPlanificacion({
      periodoId: 'per-1', carreraId: 'c-1', materiaId: 'm-1', docenteId: null,
      laboratorioId: 'l-1', diaSemana: 'LUNES', horaInicio: '07:00', horaFin: '09:00', observacion: '',
    })
    await operational.editarPlanificacion('b-1', {
      periodoId: 'per-1', carreraId: 'c-1', materiaId: 'm-1', docenteId: null,
      laboratorioId: 'l-1', diaSemana: 'LUNES', horaInicio: '07:00', horaFin: '09:00', observacion: '',
    })
    await operational.accionPlanificacion('b-1', 'enviar')
    await operational.accionPlanificacion('b-1', 'aceptar', { detalle: 'ok' })
    await operational.rechazarPlanificacion('b-1', 'Rechazo bloque')
    await operational.proponerPlanificacion('b-1', { observacion: 'Propuesta' })

    await operational.abrirAsistencia('res-1')
    await operational.abrirAsistenciaBloque('bloq-1')
    await operational.obtenerClasesDocenteHoy()
    await operational.obtenerMiHorario('per-1')
    await operational.obtenerMiHorario()
    await operational.obtenerMiHorarioDocente('per-1')
    await operational.obtenerMiHorarioDocente()
    await operational.consultarAsistencia('ses-1')
    await operational.cerrarAsistencia('ses-1')
    await operational.listarAsistentes('ses-1')
    await operational.registrarAsistencia('ses-1', 'tok-1')
    await operational.historialAsistencia('per-1')
    await operational.historialAsistencia()
    await operational.listarSesionesAbiertas()
    await operational.registrarAsistenciaPropia('ses-1')

    await operational.listarNotificaciones()
    await operational.obtenerNotificacionesNoLeidas()
    await operational.marcarNotificacionLeida('not-1')
    await operational.marcarTodasNotificacionesLeidas()

    await operational.listarSolicitudesCambio('plan-1')
    await operational.crearSolicitudCambio('plan-1', { bloqueId: 'b-1', tipo: 'LABORATORIO', motivo: 'Cambio' })
    await operational.aprobarSolicitudCambio('plan-1', 'sol-1')
    await operational.rechazarSolicitudCambio('plan-1', 'sol-1', 'No procede')
    await operational.listarSolicitudesRetiro('plan-1')
    await operational.crearSolicitudRetiro('plan-1', 'Retiro')
    await operational.aprobarSolicitudRetiro('plan-1', 'retiro-1')
    await operational.rechazarSolicitudRetiro('plan-1', 'retiro-1', 'No procede')

    // demuestra que listarIncidentes lee `contenido` (no `content`): si el
    // adapter cambiara de propiedad, esta aserción rompería con el mock actual
    expect(await operational.listarIncidentes()).toEqual(['item-contenido'])
    await operational.crearIncidente({ laboratorioEquipo: 'EQ1', descripcion: 'Fallo', prioridad: 'ALTA', fecha: '2026-01-01' })
    await operational.actualizarIncidente('inc-1', 'RESUELTO')

    expectRequests([
      ['/api/v1/planificaciones-agregadas'], ['/api/v1/planificaciones-agregadas', 'POST', JSON.stringify({ periodoId: 'per-1' })], ['/api/v1/planificaciones-agregadas/plan-1/enviar', 'POST'], ['/api/v1/planificaciones-agregadas/plan-1/retirar', 'POST'], ['/api/v1/planificaciones-agregadas/plan-1/reset-demo', 'POST'],
      ['/api/v1/planificaciones-agregadas/disponibilidad?planificacionId=plan-1&periodoId=per-1&dia=LUNES&horaInicio=07%3A00&horaFin=09%3A00'], ['/api/v1/planificaciones-agregadas/plan-1/revisiones/mi-piso/aprobar', 'POST'], ['/api/v1/planificaciones-agregadas/plan-1/revisiones/mi-piso/rechazar', 'POST', JSON.stringify({ observacion: 'Motivo rechazo' })], ['/api/v1/planificaciones-agregadas/plan-1/revisiones/mi-piso/proponer-cambio', 'POST', JSON.stringify({ bloqueId: 'b-1', observacion: 'Obs' })],
      ['/api/v1/planificaciones'], ['/api/v1/planificaciones', 'POST', JSON.stringify({ periodoId: 'per-1', carreraId: 'c-1', materiaId: 'm-1', docenteId: null, laboratorioId: 'l-1', diaSemana: 'LUNES', horaInicio: '07:00', horaFin: '09:00', observacion: '' })], ['/api/v1/planificaciones/b-1', 'PATCH', JSON.stringify({ periodoId: 'per-1', carreraId: 'c-1', materiaId: 'm-1', docenteId: null, laboratorioId: 'l-1', diaSemana: 'LUNES', horaInicio: '07:00', horaFin: '09:00', observacion: '' })], ['/api/v1/planificaciones/b-1/enviar', 'POST'], ['/api/v1/planificaciones/b-1/aceptar', 'POST', JSON.stringify({ detalle: 'ok' })], ['/api/v1/planificaciones/b-1/rechazar', 'POST', JSON.stringify({ observacion: 'Rechazo bloque' })], ['/api/v1/planificaciones/b-1/proponer-alternativa', 'POST', JSON.stringify({ observacion: 'Propuesta' })],
      ['/api/v1/asistencias/sesiones', 'POST', JSON.stringify({ reservaId: 'res-1' })], ['/api/v1/asistencias/sesiones', 'POST', JSON.stringify({ bloqueId: 'bloq-1' })], ['/api/v1/asistencias/mis-clases-hoy'], ['/api/v1/asistencias/mi-horario?periodoId=per-1'], ['/api/v1/asistencias/mi-horario'], ['/api/v1/asistencias/mi-horario-docente?periodoId=per-1'], ['/api/v1/asistencias/mi-horario-docente'], ['/api/v1/asistencias/sesiones/ses-1'], ['/api/v1/asistencias/sesiones/ses-1/cerrar', 'POST'], ['/api/v1/asistencias/sesiones/ses-1/registros'], ['/api/v1/asistencias/sesiones/ses-1/registros', 'POST', JSON.stringify({ token: 'tok-1' })], ['/api/v1/asistencias/historial?periodoId=per-1'], ['/api/v1/asistencias/historial'], ['/api/v1/asistencias/sesiones/abiertas'], ['/api/v1/asistencias/sesiones/ses-1/registro-propio', 'POST'],
      ['/api/v1/notificaciones'], ['/api/v1/notificaciones/no-leidas'], ['/api/v1/notificaciones/not-1/leer', 'POST'], ['/api/v1/notificaciones/leer-todas', 'POST'], ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-cambio'], ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-cambio', 'POST', JSON.stringify({ bloqueId: 'b-1', tipo: 'LABORATORIO', motivo: 'Cambio' })], ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-cambio/sol-1/aprobar', 'POST', JSON.stringify({ observacion: '' })], ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-cambio/sol-1/rechazar', 'POST', JSON.stringify({ observacion: 'No procede' })],
      ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-retiro'], ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-retiro', 'POST', JSON.stringify({ motivo: 'Retiro' })], ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-retiro/retiro-1/aprobar', 'POST', JSON.stringify({ observacion: '' })], ['/api/v1/planificaciones-agregadas/plan-1/solicitudes-retiro/retiro-1/rechazar', 'POST', JSON.stringify({ observacion: 'No procede' })],
      ['/api/v1/incidentes?tamanio=100'], ['/api/v1/incidentes', 'POST', JSON.stringify({ laboratorioEquipo: 'EQ1', descripcion: 'Fallo', prioridad: 'ALTA', fecha: '2026-01-01' })], ['/api/v1/incidentes/inc-1/estado', 'PATCH', JSON.stringify({ estado: 'RESUELTO' })],
    ])
  })

  it('cubre funciones de contexto y administradores en usuariosApi', async () => {
    // listarAdministradores es la única llamada paginada de este bloque: responde
    // con `content` (no `contenido`) para demostrar qué propiedad lee realmente
    // usuariosApi.listarAdministradores; el resto de endpoints no son paginados.
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url === '/api/v1/administradores?size=100') {
        return new Response(JSON.stringify({ content: ['item-content'] }), { status: 200 })
      }
      return new Response(JSON.stringify([{ id: 'ctx-1' }]), { status: 200 })
    })

    await usuarios.obtenerPerfil('p-1')
    await usuarios.actualizarPerfil('p-1', {
      identificacion: '123', nombres: 'A', apellidos: 'B', emailInstitucional: 'a@b.com',
      emailPersonal: '', telefono: '', direccion: '', fechaNacimiento: '2000-01-01', fotoUrl: null,
    })
    await usuarios.cambiarEstadoPerfil('p-1', true)
    await usuarios.obtenerPerfilPropio()
    await usuarios.actualizarPerfilPropio({
      emailPersonal: 'p@b.com', telefono: '0999', direccion: 'Dir', fotoUrl: null,
    })
    await usuarios.actualizarUsuarioInstitucionalCompleto('p-1', {
      authId: 'auth-1', username: 'user1', email: 'u@b.com', rol: 'DOCENTE', activo: true,
      pisoId: null, carreraId: null, identificacion: '123', nombres: 'A', apellidos: 'B',
      emailInstitucional: 'a@b.com', emailPersonal: '', telefono: '', direccion: '',
      fechaNacimiento: '2000-01-01', fotoUrl: null,
    })
    await usuarios.obtenerMiContextoAcademico()
    await usuarios.confirmarMiContextoAcademico({ carreraId: 'c1', periodoId: 'p1', nivel: 2 })
    await usuarios.obtenerMisContextosAcademicos()
    await usuarios.obtenerContextosAcademicos('perf-1')
    await usuarios.asignarContextoAcademico('perf-1', { carreraId: 'c1', periodoId: 'p1', nivel: 2 })
    await usuarios.obtenerDocenteResumen('doc-1')
    // demuestra que listarAdministradores lee `content` (no `contenido`)
    expect(await usuarios.listarAdministradores()).toEqual(['item-content'])
    await usuarios.actualizarAdministrador({
      id: 'adm-1', perfilId: 'p-1', codigoAdministrador: 'ADM', cargo: 'Cargo', pisoId: 'piso-1', activo: true,
    }, 'piso-2')
    await usuarios.obtenerAsociacionRol('perf-1')
    await usuarios.actualizarAsociacionRol('perf-1', { rol: 'ADMIN', pisoId: 'p1', carreraId: null })

    expect(fetchSpy).toHaveBeenCalledTimes(16)
    const requests = fetchSpy.mock.calls.map(([url, init]) => ({ url, method: init?.method ?? 'GET', body: init?.body }))
    expect(requests).toEqual([
      { url: '/api/v1/perfiles/p-1', method: 'GET', body: undefined },
      {
        url: '/api/v1/perfiles/p-1',
        method: 'PUT',
        body: JSON.stringify({
          identificacion: '123', nombres: 'A', apellidos: 'B', emailInstitucional: 'a@b.com',
          emailPersonal: '', telefono: '', direccion: '', fechaNacimiento: '2000-01-01', fotoUrl: null,
        }),
      },
      { url: '/api/v1/perfiles/p-1/estado', method: 'PATCH', body: JSON.stringify({ activo: true }) },
      { url: '/api/v1/perfiles/me', method: 'GET', body: undefined },
      { url: '/api/v1/perfiles/me', method: 'PATCH', body: JSON.stringify({ emailPersonal: 'p@b.com', telefono: '0999', direccion: 'Dir', fotoUrl: null }) },
      {
        url: '/api/v1/perfiles/administracion-usuarios/p-1',
        method: 'PUT',
        body: JSON.stringify({
          authId: 'auth-1',
          perfil: {
            identificacion: '123', nombres: 'A', apellidos: 'B', emailInstitucional: 'a@b.com',
            emailPersonal: '', telefono: '', direccion: '', fechaNacimiento: '2000-01-01', fotoUrl: null,
          },
          username: 'user1', email: 'u@b.com', rol: 'DOCENTE', activo: true, pisoId: null, carreraId: null,
        }),
      },
      { url: '/api/v1/estudiantes/mi-contexto', method: 'GET', body: undefined },
      { url: '/api/v1/estudiantes/mi-contexto', method: 'POST', body: JSON.stringify({ carreraId: 'c1', periodoId: 'p1', nivel: 2 }) },
      { url: '/api/v1/estudiantes/mis-contextos', method: 'GET', body: undefined },
      { url: '/api/v1/estudiantes/perfil/perf-1/contextos', method: 'GET', body: undefined },
      { url: '/api/v1/estudiantes/perfil/perf-1/contextos', method: 'POST', body: JSON.stringify({ carreraId: 'c1', periodoId: 'p1', nivel: 2 }) },
      { url: '/api/v1/docentes/doc-1/resumen', method: 'GET', body: undefined },
      { url: '/api/v1/administradores?size=100', method: 'GET', body: undefined },
      {
        url: '/api/v1/administradores/adm-1',
        method: 'PUT',
        body: JSON.stringify({
          perfilId: 'p-1', codigoAdministrador: 'ADM', cargo: 'Cargo', pisoId: 'piso-2', activo: true,
        }),
      },
      { url: '/api/v1/perfiles/perf-1/asociacion-rol', method: 'GET', body: undefined },
      { url: '/api/v1/perfiles/perf-1/asociacion-rol', method: 'PUT', body: JSON.stringify({ rol: 'ADMIN', pisoId: 'p1', carreraId: null }) },
    ])
    fetchSpy.mockRestore()
  })
})
