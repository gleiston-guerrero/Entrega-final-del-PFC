package ec.edu.scli.reservas.infrastructure.notification;

import com.google.firebase.messaging.*;
import ec.edu.scli.reservas.domain.port.out.NotificationPort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@ConditionalOnProperty(name = "app.notifications.firebase.enabled", havingValue = "true")
public class FirebaseNotificationAdapter implements NotificationPort {

    private static final Logger log = LoggerFactory.getLogger(FirebaseNotificationAdapter.class);

    private final FirebaseMessaging messaging;

    public FirebaseNotificationAdapter(FirebaseMessaging messaging) {
        this.messaging = messaging;
    }

    @Override
    public void enviar(String token, String titulo, String cuerpo, Map<String, String> datos) {
        try {
            String messageId = messaging.send(
                    Message.builder()
                            .setToken(token)
                            .setNotification(
                                    Notification.builder()
                                            .setTitle(titulo)
                                            .setBody(cuerpo)
                                            .build()
                            )
                            .putAllData(datos)
                            .build()
            );

            log.info(
                    "FCM enviado correctamente messageId={} tipo={} incidenteId={}",
                    messageId,
                    datos.getOrDefault("tipo", "N/A"),
                    datos.getOrDefault("incidenteId", "N/A")
            );

        } catch (FirebaseMessagingException exception) {
            log.error(
                    "Error al enviar notificacion FCM tipo={} incidenteId={} codigo={}",
                    datos.getOrDefault("tipo", "N/A"),
                    datos.getOrDefault("incidenteId", "N/A"),
                    exception.getMessagingErrorCode(),
                    exception
            );

            throw new IllegalStateException(
                    "No se pudo enviar la notificación",
                    exception
            );
        }
    }
}
