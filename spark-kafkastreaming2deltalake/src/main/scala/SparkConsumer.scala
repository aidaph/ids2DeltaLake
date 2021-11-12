import io.delta.tables._
import org.apache.spark._
import org.apache.log4j.Logger
import org.apache.spark.streaming._
import org.apache.kafka.common.serialization.StringDeserializer
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.sql.streaming.Trigger
import org.apache.spark.sql.types._
import org.apache.spark.sql.types.DataType
import org.apache.spark.sql.execution.streaming.FileStreamSource.Timestamp
import org.apache.spark.streaming.kafka010._
import org.apache.spark.streaming.kafka010.LocationStrategies.PreferConsistent
import org.apache.spark.streaming.kafka010.ConsumerStrategies.Subscribe


object SparkConsumer {

  val localLogger = Logger.getLogger("SparkConsumer")

  def main(args: Array[String]){

    val sparkConf = new SparkConf()
      .setMaster("local[4]")
      .setAppName("TestKafkaSparkStreaming")

    val sparkSession = SparkSession.builder().config(sparkConf).getOrCreate()

    // Define the context = entry point for Spark Streaming
    val streamingContext = new StreamingContext(sparkSession.sparkContext, Seconds(3))

    val kafkaParams = Map[String, Object](
      "bootstrap.servers" -> "<kafka-ip>:9092",
      "key.deserializer" -> classOf[StringDeserializer],
      "value.deserializer" -> classOf[StringDeserializer],
      "group.id" -> "kafka_streaming_group",
      "auto.offset.reset" -> "latest",
      "enable.auto.commit" -> (false: java.lang.Boolean)
    )

    val kafkaBroker = "<kafka-ip>:9092"
    val topics = Array("connect-test")
    /* val stream = KafkaUtils.createDirectStream[String,String](
      streamingContext,
      PreferConsistent,
      Subscribe[String,String](topics,kafkaParams)
    )*/
    import org.apache.spark.sql.Encoders
    val spark = SparkSession
      .builder()
      .getOrCreate()


    val DEFAULT_MAX_TO_STRING_FIELDS = 100

    val jsonSchema = StructType(Array(
          StructField("seconds", IntegerType),
          StructField("action", StringType),
          StructField("class", StringType),
          StructField("dir", StringType),
          StructField("dst_ad", StringType),
          StructField("dst_ap", StringType),
          StructField("dst_port", StringType),
          StructField("eth_dst", StringType),
          StructField("eth_len", IntegerType),
          StructField("eth_src", StringType),
          StructField("eth_type", StringType),
          StructField("gid", IntegerType),
          StructField("iface", StringType),
          StructField("ip_id", IntegerType),
          StructField("ip_len", IntegerType),
          StructField("msg", StringType),
          StructField("mpls", IntegerType),
          StructField("pkt_num", IntegerType),
          StructField("priority", IntegerType),
          StructField("proto", StringType),
          StructField("rev", IntegerType),
          StructField("rule", StringType),
          StructField("service", StringType),
          StructField("sid", IntegerType),
          StructField("src_addr", StringType),
          StructField("src_ap", StringType),
          StructField("src_port", IntegerType),
          StructField("cp_ack", IntegerType),
          StructField("tcp_flags", StringType),
          StructField("tcp_len", IntegerType),
          StructField("tcp_seq", IntegerType),
          StructField("tcp_win", IntegerType),
          StructField("tos", IntegerType),
          StructField("ttl", IntegerType),
          StructField("vlan", IntegerType),
          StructField("timestamp", StringType),
          StructField("b64_data", StringType)
    ))

    val u2Schema = StructType(Array(
      StructField("sensor-id", IntegerType),
      StructField("event-id", IntegerType),
      StructField("event-second", IntegerType),
      StructField("packend-second", IntegerType),
      StructField("packet-microsecond", IntegerType),
      StructField("linktype", IntegerType),
      StructField("length", IntegerType),
      StructField("data", StringType),
      StructField("event-microsecond", IntegerType),
      StructField("generator-id", IntegerType),
      StructField("signature-id", IntegerType),
      StructField("signature-revision", IntegerType),
      StructField("classification-id", IntegerType),
      StructField("priority", IntegerType),
      StructField("source-ip", StringType),
      StructField("destination-ip", StringType),
      StructField("sport-itype", IntegerType),
      StructField("dport-icode", IntegerType),
      StructField("protocol", IntegerType),
      StructField("impact-flag", IntegerType),
      StructField("impact", IntegerType),
      StructField("blocked", IntegerType),
      StructField("mpls-label", StringType),
      StructField("vlan-id", IntegerType),
      StructField("pad2", IntegerType),
      StructField("appid", IntegerType)
    ))

    val dfu2 = sparkSession.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers","<kafka-ip>:9092")
      .option("subscribe", "snort3-U2events")
      .load()
      .select(col("value").cast("string"))

    val dfjson = sparkSession.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers","<kafka-ip>:9092")
      .option("subscribe", "snort3-json")
      .load()
      .select(col("value").cast("string"))

    localLogger.info(s"connecting to brokers: $kafkaBroker")
    localLogger.info(s"kafkaParams: $kafkaParams")
    localLogger.info(s"topics: $topics")

    //stream.map(record => (record.key, record.value))

    //stream.print()
    //streamingContext.start()
    //val df1 = dfu2.select("value")
    //.select(from_json(col("value"), u2Schema).as("data"))
    //.select("data.*")
    val df_json = dfjson.select("value")
    .select(from_json(col("value"), jsonSchema).as("data"))
    .select("data.*")

    /* Export data to a persistence dataset in HDFS */
    df_json.writeStream 
        .format("delta")
        .trigger(Trigger.ProcessingTime("60 seconds")) // only change in query
        .queryName("kafkaStreams")
        .outputMode("append")
        .option("checkpointLocation","hdfs://<hadoop-namenode>:9820/snort-events/_checkpoints/elt-from-json")
        .start("hdfs://<hadoop-namenode>:9820/snort-events")
        .awaitTermination()
  }  
}
