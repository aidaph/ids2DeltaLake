import org.apache.log4j.{Level, Logger}
import org.apache.spark.SparkContext

object SparkDemo {
  def main(args: Array[String]): Unit = {
    val sc = new SparkContext("local[*]", "SparkDemo")

    val lines = sc.textFile("/home/aidaph/Documentos/development/HandsOn_Scala/example.txt")
    val words = lines.flatMap(line => line.split(' '))

    val wordsKVRdd = words.map(x => (x,1))

    val count = wordsKVRdd.reduceByKey((x,y) => x + y).map(x => (x._2,x._1)).sortByKey(false).map(x => (x._2, x._1)).take(10)
count.foreach(println)
  }


}
