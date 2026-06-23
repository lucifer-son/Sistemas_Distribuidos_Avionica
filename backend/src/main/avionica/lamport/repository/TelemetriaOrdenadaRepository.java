package avionica.lamport.repository;

import avionica.lamport.model.TelemetriaOrdenada;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TelemetriaOrdenadaRepository extends JpaRepository<TelemetriaOrdenada, Long> {
}
